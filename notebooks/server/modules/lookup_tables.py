###### IMPORT MODULES ######
import numpy as np
from numba import njit

###### DEFINE UTILITARY FUNCTIONS ######

# Lookup table to map mz value to indexes in array_spectra
@njit
def build_index_lookup_table(array_spectra, array_pixel_indexes, divider_lookup):
    """[summary]

    Args:
        array_spectra ([type]): [description]
        array_pixel_indexes ([type]): [description]
        divider_lookup ([type]): [description]

    Returns:
        [type]: [description]
    """
    # for each pixel, lookup gives the first index of mz such that mz>=lookup*divider_lookup
    # if no such mz, lookup gives last possible mz index (i.e. bigger possible mz for the current pixel, but under the lookup)
    # if lookup*divider_lookup is bigger than the smallest mz, lookup returns the first mz index possible for the current pixel, above the current lookup
    # if no peak at all in the spectrum... lookup return -1

    size_spectrum = 2000

    lookup_table = np.zeros((size_spectrum // divider_lookup, array_pixel_indexes.shape[0]), dtype=np.int32)
    lookup_table[0, :] = array_pixel_indexes[:, 0]
    for idx_pix in range(array_pixel_indexes.shape[0]):
        j = array_pixel_indexes[idx_pix, 0]

        # if there's no peak for the current pixel, lookup is -1
        if j == -1:
            for i in range(size_spectrum // divider_lookup):
                lookup_table[i, idx_pix] = -1

        for index_lookup in range(size_spectrum // divider_lookup - 1):

            # else first find the first mz index corresponding to current lookup for current pixel (skipped if current mz>lookup)
            while array_spectra[0, j] < ((index_lookup + 1) * divider_lookup):
                j += 1
                if j == array_pixel_indexes[idx_pix, 1] + 1:
                    break

            # check that we're still in the good pixel and add mz index to lookup
            if j < array_pixel_indexes[idx_pix, 1] + 1:
                lookup_table[index_lookup + 1, idx_pix] = j

            # if we're not in the good pixel, this means that the while loop was exited because the lookup didn't exist, so we fill the rest of the table with biggest possible value
            else:
                for i in range(index_lookup + 1, size_spectrum // divider_lookup):
                    lookup_table[i, idx_pix] = j - 1
                break

    return lookup_table


# Lookup table to map mz value to image of cumulated spectrum until this mz value
@njit
def build_cumulated_image_lookup_table(array_spectra, array_pixel_indexes, img_shape, divider_lookup):
    """[summary]

    Args:
        array_spectra ([type]): [description]
        array_pixel_indexes ([type]): [description]
        img_shape ([type]): [description]
        divider_lookup ([type]): [description]

    Returns:
        [type]: [description]
    """
    size_spectrum = 2000

    image_lookup_table = np.zeros((size_spectrum // divider_lookup, img_shape[0], img_shape[1]), dtype=np.float32)
    image_lookup_table[0, :] = np.zeros((img_shape[0], img_shape[1]), dtype=np.float32)
    for idx_pix in range(array_pixel_indexes.shape[0]):
        j = array_pixel_indexes[idx_pix, 0]
        # if current pixel contains no peak, just skip to next one and add nothing
        if j == -1:
            continue

        pix_value = 0
        coor_pix = convert_spectrum_index_to_coordinate(idx_pix, img_shape)
        for index_lookup in range(size_spectrum // divider_lookup - 1):
            while array_spectra[0, j] >= (index_lookup * divider_lookup) and array_spectra[0, j] < (
                (index_lookup + 1) * divider_lookup
            ):
                pix_value += array_spectra[1, j]
                j += 1
                if j == array_pixel_indexes[idx_pix, 1] + 1:
                    break

            if j < array_pixel_indexes[idx_pix, 1] + 1:
                image_lookup_table[index_lookup + 1, coor_pix[0], coor_pix[1]] = pix_value
            else:
                for i in range(index_lookup + 1, size_spectrum // divider_lookup):
                    image_lookup_table[i, coor_pix[0], coor_pix[1]] = pix_value
                break

    return image_lookup_table


# Build a new lookup table to compute fast the indexes corresponding to the boundaries selected on dash
@njit
def build_index_lookup_table_averaged_spectrum(array_mz):
    size_spectrum = 2000
    lookup_table = np.empty((size_spectrum), dtype=np.int32)
    j = 0
    lookup_table[0] = 0
    for index_lookup in range(size_spectrum - 1):
        while array_mz[j] < index_lookup + 1:
            j += 1
            if j == array_mz.shape[0]:
                break

        if j < array_mz.shape[0]:
            lookup_table[index_lookup + 1] = j
        else:
            for i in range(index_lookup + 1, size_spectrum):
                lookup_table[i] = j - 1
            break

    return lookup_table


# Extend the averaged spectra with zeros to be able to plot them with scatterplotgl
@njit
def add_zeros_to_spectrum(array_spectra, pad_individual_peaks=False):
    """[summary]

    Args:
        array_spectra ([type]): [description]
        pad_individual_peaks (bool, optional): [description]. Defaults to False.

    Returns:
        [type]: [description]
    """
    # for speed, allocate array of maximum size
    new_array_spectra = np.zeros((array_spectra.shape[0], array_spectra.shape[1] * 3), dtype=np.float32)

    if pad_individual_peaks:
        pad = 0
        # print(np.min(array_spectra[0,1:]-array_spectra[0,:-1]))
        for i in range(array_spectra.shape[1] - 1):

            # if there's a discontinuity between two peaks, pad with zeros
            if array_spectra[0, i + 1] - array_spectra[0, i] >= 2 * 10 ** -4:
                # print("discontuinuity detected")
                # break
                # add left peak
                new_array_spectra[0, i + pad] = array_spectra[0, i]
                new_array_spectra[1, i + pad] = array_spectra[1, i]

                # add zero to the right of left peak
                pad += 1
                new_array_spectra[0, i + pad] = array_spectra[0, i] + 10 ** -5
                new_array_spectra[1, i + pad] = 0

                # add zero to the left of right peak
                pad += 1
                new_array_spectra[0, i + pad] = array_spectra[0, i + 1] - 10 ** -5
                new_array_spectra[1, i + pad] = 0

                # right peak added in the next loop iteration
            else:
                # print("two near peaks")
                new_array_spectra[0, i + pad] = array_spectra[0, i]
                new_array_spectra[1, i + pad] = array_spectra[1, i]

        new_array_spectra[0, array_spectra.shape[1] + pad - 1] = array_spectra[0, -1]
        new_array_spectra[1, array_spectra.shape[1] + pad - 1] = array_spectra[1, -1]
        return new_array_spectra[:, : array_spectra.shape[1] + pad]

    else:
        for i in range(array_spectra.shape[1]):
            # store old array in a regular grid in the extended array
            new_array_spectra[0, 3 * i + 1] = array_spectra[0, i]
            new_array_spectra[1, 3 * i + 1] = array_spectra[1, i]

            # add zeros in the remaining slots
            new_array_spectra[0, 3 * i] = array_spectra[0, i] - 10 ** -4
            new_array_spectra[0, 3 * i + 2] = array_spectra[0, i] + 10 ** -4

        return new_array_spectra


def process_lookup_tables(t_index_name, l_arrays_raw_data=None, load_from_file=True, test=False, save=True):
    """[summary]

    Args:
        t_index_name ([type]): [description]
        l_arrays_raw_data ([type], optional): [description]. Defaults to None.
        load_from_file (bool, optional): [description]. Defaults to True.
        test (bool, optional): [description]. Defaults to False.
        save (bool, optional): [description]. Defaults to True.

    Returns:
        [type]: [description]
    """

    if l_arrays_raw_data is not None:
        (
            array_pixel_indexes_high_res,
            array_spectra_high_res,
            array_averaged_mz_intensity_low_res,
            array_averaged_mz_intensity_high_res,
            image_shape,
        ) = l_arrays_raw_data

    elif load_from_file:

        # get slice path
        index_slice = t_index_name[0]
        name = t_index_name[1]
        try:
            appendix = "_unfiltered"
            if len(t_index_name) > 2:
                path = "data/slice_" + str(index_slice) + "_bis" + appendix + ".npz"
                npzfile = np.load(path)
                # annotate repeated slice by multiplying their index by thousand (easier than replacing slice name with a non-int like bis)
                path = "data/slice_" + str(index_slice * 1000) + appendix + ".npz"
            else:
                path = "data/slice_" + str(index_slice) + appendix + ".npz"
                npzfile = np.load(path)
        except:
            appendix = "_filtered"
            if len(t_index_name) > 2:
                path = "data/slice_" + str(index_slice) + "_bis" + appendix + ".npz"
                npzfile = np.load(path)
                # annotate repeated slice by multiplying their index by thousand (easier than replacing slice name with a non-int like bis)
                path = "data/slice_" + str(index_slice * 1000) + appendix + ".npz"
            else:
                path = "data/slice_" + str(index_slice) + appendix + ".npz"
                npzfile = np.load(path)

        # load individual arrays
        array_pixel_indexes_high_res = npzfile["array_pixel_indexes_high_res"]
        array_spectra_high_res = npzfile["array_spectra_high_res"]
        array_averaged_mz_intensity_low_res = npzfile["array_averaged_mz_intensity_low_res"]
        array_averaged_mz_intensity_high_res = npzfile["array_averaged_mz_intensity_high_res"]
        image_shape = npzfile["image_shape"]

        if "divider_lookup" in npzfile:
            print("This file has already been processed before")
            return None
    else:
        print("Either the data or a filename must be provided")
        return None

    # define divider_lookup
    divider_lookup = 10

    # buid lookup table linking mz value to index in array_spectra for each pixel
    lookup_table_spectra_high_res = build_index_lookup_table(
        array_spectra_high_res, array_pixel_indexes_high_res, divider_lookup
    )
    print(
        "Size (in mb) of lookup_table_spectra_high_res: ", round(lookup_table_spectra_high_res.nbytes / 1024 / 1024, 2)
    )
    print("Shape of lookup_table_spectra_high_res: ", lookup_table_spectra_high_res.shape)
    if test:
        # value should be equal or > to 50*10
        print(
            "Following values should be >= to 500: (very high values correspond to -1, i.e. no peak in pixel)",
            array_spectra_high_res[0, lookup_table_spectra_high_res[50]],
        )

    # build lookup table of the cumulated spectrum for each pixel
    cumulated_image_lookup_table_high_res = build_cumulated_image_lookup_table(
        array_spectra_high_res, array_pixel_indexes_high_res, image_shape, divider_lookup
    )
    print(
        "Size (in mb) of cumulated_image_lookup_table_high_res: ",
        round(cumulated_image_lookup_table_high_res.nbytes / 1024 / 1024, 2),
    )
    print("Shape of cumulated_image_lookup_table_high_res: ", cumulated_image_lookup_table_high_res.shape)

    # build lookup table to compute fast the indexes corresponding to the boundaries selected on dash
    lookup_table_averaged_spectrum_high_res = build_index_lookup_table_averaged_spectrum(
        array_mz=array_averaged_mz_intensity_high_res[0, :]
    )
    print(
        "Size (in mb) of lookup_table_averaged_spectrum_high_res: ",
        round(lookup_table_averaged_spectrum_high_res.nbytes / 1024 / 1024, 2),
    )
    print("Shape of lookup_table_averaged_spectrum_high_res: ", lookup_table_averaged_spectrum_high_res.shape)

    # extend averaged arrays with zeros for nicer display
    array_averaged_mz_intensity_low_res = add_zeros_to_spectrum(
        array_averaged_mz_intensity_low_res, pad_individual_peaks=True
    )
    array_averaged_mz_intensity_high_res = add_zeros_to_spectrum(
        array_averaged_mz_intensity_high_res, pad_individual_peaks=True
    )

    # normalize spectrum
    array_averaged_mz_intensity_low_res[1, :] /= np.sum(array_averaged_mz_intensity_low_res[1, :])
    array_averaged_mz_intensity_high_res[1, :] /= np.sum(array_averaged_mz_intensity_high_res[1, :])
    for (b1, b2) in array_pixel_indexes_high_res:
        array_spectra_high_res[1, b1 : b2 + 1] /= np.sum(array_spectra_high_res[1, b1 : b2 + 1])

    if save:
        # save as npz file
        print("Saving...")
        np.savez(
            path,
            array_pixel_indexes_high_res=array_pixel_indexes_high_res,
            array_spectra_high_res=array_spectra_high_res,
            array_averaged_mz_intensity_low_res=array_averaged_mz_intensity_low_res,
            array_averaged_mz_intensity_high_res=array_averaged_mz_intensity_high_res,
            image_shape=image_shape,
            divider_lookup=divider_lookup,
            lookup_table_spectra_high_res=lookup_table_spectra_high_res,
            cumulated_image_lookup_table_high_res=cumulated_image_lookup_table_high_res,
            lookup_table_averaged_spectrum_high_res=lookup_table_averaged_spectrum_high_res,
        )

