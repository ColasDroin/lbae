###### IMPORT MODULES ######

# Standard modules
import numpy as np
from numba import njit

# Homemade package
from modules.tools.spectra import convert_spectrum_idx_to_coor, add_zeros_to_spectrum

###### DEFINE UTILITY FUNCTIONS ######
@njit
def build_index_lookup_table(
    array_spectra, array_pixel_indexes, divider_lookup, size_spectrum=2000
):
    """This function builds a lookup table to map mz values to indexes in array_spectra. In practice, for each pixel,
    the lookup table gives the first index of mz such that mz>=lookup*divider_lookup. If no such mz exists, the lookup 
    table gives last possible mz index (i.e. biggest possible mz for the current pixel, but under the lookup). If 
    lookup*divider_lookup is smaller than the smallest mz, it returns the first mz index possible for the current pixel, 
    above the current lookup. If there are no peak at all in the spectrum... it returns -1.

    Args:
        array_spectra (np.ndarray): An array of shape (2,n) containing spectrum data (m/z and intensity) for each pixel.
        array_pixel_indexes (np.ndarray): An array of shape (m,2) containing the boundary indices of each pixel in 
            array_spectra. 
        divider_lookup (int): Sets the resolution of the lookup table. The bigger it is, the bigger the increments 
            between two successive lookups. Must be consistent across lookup tables.
        size_spectrum (int): The total size of the spectrum indexed by the lookup. Defaults to 2000, corresponding to
            an indexed spectrum ranging from 0 m/z to 2000 m/z.

    Returns:
        np.ndarray: An array of shape (size_spectrum// divider_lookup, m), mapping m/z values to indexes in 
            array_spectra for each pixel.
    """
    # Define the empty array for the lookup table
    lookup_table = np.zeros(
        (size_spectrum // divider_lookup, array_pixel_indexes.shape[0]), dtype=np.int32
    )
    lookup_table[0, :] = array_pixel_indexes[:, 0]

    # Loop over pixel indexes
    for idx_pix in range(array_pixel_indexes.shape[0]):
        j = array_pixel_indexes[idx_pix, 0]

        # If there's no peak for the current pixel, lookup is -1
        if j == -1:
            for i in range(size_spectrum // divider_lookup):
                lookup_table[i, idx_pix] = -1

        # Loop over lookup indexes
        for index_lookup in range(size_spectrum // divider_lookup - 1):

            # First find the first mz index corresponding to current lookup for current pixel
            # (skipped if current mz>lookup)
            while array_spectra[0, j] < ((index_lookup + 1) * divider_lookup):
                j += 1
                if j == array_pixel_indexes[idx_pix, 1] + 1:
                    break

            # Check that we're still in the requested pixel and add mz index to lookup
            if j < array_pixel_indexes[idx_pix, 1] + 1:
                lookup_table[index_lookup + 1, idx_pix] = j

            # If we're not in the requested pixel, this means that the while loop was exited because the lookup didn't
            # exist, so we fill the rest of the table with biggest possible value
            else:
                for i in range(index_lookup + 1, size_spectrum // divider_lookup):
                    lookup_table[i, idx_pix] = j - 1
                break

    return lookup_table


# Lookup table to
@njit
def build_cumulated_image_lookup_table(
    array_spectra, array_pixel_indexes, img_shape, divider_lookup, size_spectrum=2000
):
    """This function builds a lookup table to map the mz values to the image consisting of cumulated spectrum 
    (for each pixel) until this mz value.

    Args:
        array_spectra (np.ndarray): An array of shape (2,n) containing spectrum data (m/z and intensity) for each pixel.
        array_pixel_indexes (np.ndarray): An array of shape (m,2) containing the boundary indices of each pixel in 
            array_spectra. 
        img_shape ([type]): [description]
        divider_lookup (int): Sets the resolution of the lookup table. The bigger it is, the bigger the increments 
            between two successive lookups. Must be consistent across lookup tables.
        size_spectrum (int): The total size of the spectrum indexed by the lookup. Defaults to 2000, corresponding to
            an indexed spectrum ranging from 0 m/z to 2000 m/z.

    Returns:
        np.ndarray: An array of shape (size_spectrum// divider_lookup, image height, image_width), mapping m/z values to 
            the cumulated spectrum until the corresponding m/z value for each pixel.
    """
    # Define the empty array for the lookup table
    image_lookup_table = np.zeros(
        (size_spectrum // divider_lookup, img_shape[0], img_shape[1]), dtype=np.float32
    )
    image_lookup_table[0, :] = np.zeros((img_shape[0], img_shape[1]), dtype=np.float32)
    for idx_pix in range(array_pixel_indexes.shape[0]):
        j = array_pixel_indexes[idx_pix, 0]
        # If current pixel contains no peak, just skip to next one and add nothing
        if j == -1:
            continue
        pix_value = 0
        coor_pix = convert_spectrum_idx_to_coor(idx_pix, img_shape)

        # Loop over lookup indexes
        for index_lookup in range(size_spectrum // divider_lookup - 1):

            # Find the first mz index corresponding to current lookup for current pixel
            # (skipped if current mz>lookup)
            while array_spectra[0, j] >= (index_lookup * divider_lookup) and array_spectra[0, j] < (
                (index_lookup + 1) * divider_lookup
            ):
                pix_value += array_spectra[1, j]
                j += 1
                if j == array_pixel_indexes[idx_pix, 1] + 1:
                    break

            # Check that we're still in the good pixel and add mz index to lookup
            if j < array_pixel_indexes[idx_pix, 1] + 1:
                image_lookup_table[index_lookup + 1, coor_pix[0], coor_pix[1]] = pix_value

            # If we're not in the requested pixel, this means that the while loop was exited because the lookup didn't
            # exist, so we fill the rest of the table with biggest possible value
            else:
                for i in range(index_lookup + 1, size_spectrum // divider_lookup):
                    image_lookup_table[i, coor_pix[0], coor_pix[1]] = pix_value
                break

    return image_lookup_table


# Build a new lookup table to compute fast the indexes corresponding to the boundaries selected on dash
@njit
def build_index_lookup_table_averaged_spectrum(array_mz, size_spectrum=2000):
    """This function builds a lookup table identical to the one defined in build_index_lookup_table(), except that this
    one maps mz values to indexes in the averaged array_spectra (across all pixels).

    Args:
        array_mz (np.ndarray): The m/z array of the averaged array spectra (i.e. row 0).
        size_spectrum (int): The total size of the spectrum indexed by the lookup. Defaults to 2000, corresponding to
            an averaged indexed spectrum ranging from 0 m/z to 2000 m/z.

    Returns:
        np.ndarray: An array of length size_spectrum (i.e. the defaults divider_lookup is 1 for this array), 
            mapping m/z values to indexes in the averaged array_spectra.
    """
    # Define the empty array for the lookup table
    lookup_table = np.empty((size_spectrum), dtype=np.int32)
    j = 0
    lookup_table[0] = 0

    # Loop over lookup indexes
    for index_lookup in range(size_spectrum - 1):

        # Find the first mz index corresponding to current lookup for current pixel
        while array_mz[j] < index_lookup + 1:
            j += 1
            if j == array_mz.shape[0]:
                break

        # Add the lookup to the table if it exists
        if j < array_mz.shape[0]:
            lookup_table[index_lookup + 1] = j

        # If the lookup doesn't exist, so we fill the rest of the table with biggest possible m/z value
        else:
            for i in range(index_lookup + 1, size_spectrum):
                lookup_table[i] = j - 1
            break

    return lookup_table


def process_lookup_tables(
    t_index_path,
    temp_path="notebooks/server/data/temp/",
    l_arrays_raw_data=None,
    load_from_file=True,
    save=True,
    return_result=False,
):
    """This function has been implemented to allow the paralellization of lookup tables processing. It computes and
    returns/saves the lookup tables for each slice. The output consists of:
    - array_pixel_indexes_high_res: of shape (n,2), it maps each pixel to two array_spectra_high_res indices, delimiting
      the corresponding spectrum.
    - array_spectra_high_res: of shape (2,m), it contains the concatenated spectra of each pixel. First row contains the
      m/z values, while second row contains the corresponding intensities.
    - array_averaged_mz_intensity_low_res: of shape (2, k), it contains the low-resolution spectrum averaged over all 
      pixels. First row contains the m/z values, while second row contains the corresponding intensities.
    - array_averaged_mz_intensity_low_res: Same as array_averaged_mz_intensity_low_res, but in higher resolution, with,
      therefore, a different shape.
    - image_shape: a tuple of integers, indicating the vertical and horizontal size of the corresponding slice.
    - divider_lookup: integer that sets the resolution of the lookup tables.
    - lookup_table_spectra_high_res: of shape (size_spectrum// divider_lookup, m), it maps m/z values to indexes in 
      array_spectra for each pixel.
    - cumulated_image_lookup_table_high_res: of shape (size_spectrum// divider_lookup, image height, image_width), it 
    maps m/z values to the cumulated spectrum until the corresponding m/z value for each pixel.
    - lookup_table_averaged_spectrum_high_res: of length size_spectrum, it maps m/z values to indexes in the averaged 
      array_spectra for each pixel.


    Args:
        t_index_path (tuple(int, str)): A tuple containing the index of the slice (starting from 1) and the 
            corresponding path for the raw data.
        temp_path (str, optional): Path to load/save the output npz file. Defaults to "notebooks/server/data/temp/".
        l_arrays_raw_data (list, optional): A list of arrays containing the data that is processed in the current 
            function. If None, the same arrays must be loaded from the disk. Defaults to None.
        load_from_file (bool, optional): If True, the arrays containing the data processed by the current function are 
            loaded from the disk. If False, the corresponding arrays must be provided through the parameter 
            l_arrays_raw_data. Defaults to True.
        save (bool, optional): If True, output arrays are saved in a npz file. Defaults to True.
        return_result (bool, optional): If True, output arrays are returned by the function. Defaults to False.

    Returns:
        Depending on 'return result', returns either nothing, either several np.ndarrays, described above.
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

        # Get slice path
        slice_index = t_index_path[0]
        name = t_index_path[1]
        try:
            appendix = "_unfiltered"
            if len(t_index_path) > 2:
                path = temp_path + "slice_" + str(slice_index) + "_bis" + appendix + ".npz"
                npzfile = np.load(path)
                # Annotate repeated slice by multiplying their index by thousand (easier than replacing slice name
                # with a non-int like bis)
                path = temp_path + "slice_" + str(slice_index * 1000) + appendix + ".npz"
            else:
                path = temp_path + "slice_" + str(slice_index) + appendix + ".npz"
                npzfile = np.load(path)
        except:
            appendix = "_filtered"
            if len(t_index_path) > 2:
                path = temp_path + "slice_" + str(slice_index) + "_bis" + appendix + ".npz"
                npzfile = np.load(path)
                # Annotate repeated slice by multiplying their index by thousand (easier than replacing slice name
                # with a non-int like bis)
                path = temp_path + "slice_" + str(slice_index * 1000) + appendix + ".npz"
            else:
                path = temp_path + "slice_" + str(slice_index) + appendix + ".npz"
                npzfile = np.load(path)

        # Load individual arrays
        array_pixel_indexes_high_res = npzfile["array_pixel_indexes_high_res"]
        array_spectra_high_res = npzfile["array_spectra_high_res"]
        array_averaged_mz_intensity_low_res = npzfile["array_averaged_mz_intensity_low_res"]
        array_averaged_mz_intensity_high_res = npzfile["array_averaged_mz_intensity_high_res"]
        image_shape = npzfile["image_shape"]

        # Try to see if the array has already been processed before
        if "divider_lookup" in npzfile:
            print("This file has already been processed before")
            return None
    else:
        print("Either the data or a filename must be provided")
        return None

    # Normalize spectrum
    array_averaged_mz_intensity_low_res[1, :] /= np.sum(array_averaged_mz_intensity_low_res[1, :])
    array_averaged_mz_intensity_high_res[1, :] /= np.sum(array_averaged_mz_intensity_high_res[1, :])
    for (b1, b2) in array_pixel_indexes_high_res:
        # ? Instead of processing this way (divide by the entire pixel sum of spectra), maybe divide by the number of non-zero values in the spectrum ?
        array_spectra_high_res[1, b1 : b2 + 1] /= np.sum(array_spectra_high_res[1, b1 : b2 + 1])

    # Define divider_lookup
    divider_lookup = 1

    # Build lookup table linking mz value to index in array_spectra for each pixel
    lookup_table_spectra_high_res = build_index_lookup_table(
        array_spectra_high_res, array_pixel_indexes_high_res, divider_lookup
    )
    print(
        "Size (in mb) of lookup_table_spectra_high_res: ",
        round(lookup_table_spectra_high_res.nbytes / 1024 / 1024, 2),
    )
    print("Shape of lookup_table_spectra_high_res: ", lookup_table_spectra_high_res.shape)

    # Build lookup table of the cumulated spectrum for each pixel
    cumulated_image_lookup_table_high_res = build_cumulated_image_lookup_table(
        array_spectra_high_res, array_pixel_indexes_high_res, image_shape, divider_lookup
    )
    print(
        "Size (in mb) of cumulated_image_lookup_table_high_res: ",
        round(cumulated_image_lookup_table_high_res.nbytes / 1024 / 1024, 2),
    )
    print(
        "Shape of cumulated_image_lookup_table_high_res: ",
        cumulated_image_lookup_table_high_res.shape,
    )

    # Extend averaged arrays with zeros for nicer display
    array_averaged_mz_intensity_low_res, _ = add_zeros_to_spectrum(
        array_averaged_mz_intensity_low_res, pad_individual_peaks=True
    )
    array_averaged_mz_intensity_high_res, _ = add_zeros_to_spectrum(
        array_averaged_mz_intensity_high_res, pad_individual_peaks=True
    )

    # Build lookup table to compute fast the indexes corresponding to the boundaries selected on dash
    lookup_table_averaged_spectrum_high_res = build_index_lookup_table_averaged_spectrum(
        array_mz=array_averaged_mz_intensity_high_res[0, :]
    )
    print(
        "Size (in mb) of lookup_table_averaged_spectrum_high_res: ",
        round(lookup_table_averaged_spectrum_high_res.nbytes / 1024 / 1024, 2),
    )
    print(
        "Shape of lookup_table_averaged_spectrum_high_res: ",
        lookup_table_averaged_spectrum_high_res.shape,
    )

    if save:
        # Save as npz file
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

    # Returns all array if needed
    if return_result:
        return (
            array_pixel_indexes_high_res,
            array_spectra_high_res,
            array_averaged_mz_intensity_low_res,
            array_averaged_mz_intensity_high_res,
            image_shape,
            divider_lookup,
            lookup_table_spectra_high_res,
            cumulated_image_lookup_table_high_res,
            lookup_table_averaged_spectrum_high_res,
        )

