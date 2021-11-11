###### IMPORT MODULES ######

import numpy as np
from numba import jit
from timeit import default_timer as timer

###### DEFINE UTILITARY FUNCTIONS ######


@jit(nopython=True)
def convert_spectrum_idx_to_coor(index, shape):
    return int(index // shape[1]), int(index % shape[1])


@jit(nopython=True)
def convert_coor_to_spectrum_idx(coordinate, shape):
    ind = coordinate[0] * shape[1] + coordinate[1]
    if ind >= shape[0] * shape[1]:
        print("BUG, index not allowed")
        return -1
    return ind


# Get image between two mz value
@jit(nopython=True)
def compute_normalized_spectra(
    array_spectra, array_pixel_indexes,
):
    spectrum_sum = convert_array_to_fine_grained(array_spectra, 10 ** -3, lb=350, hb=1250) + 1
    # array_spectra_normalized = np.copy(array_spectra)
    array_spectra_normalized = np.zeros(array_spectra.shape, dtype=np.float32)

    for idx_pix in range(array_pixel_indexes.shape[0]):
        print(idx_pix / array_pixel_indexes.shape[0] * 100, " done")
        # If pixel contains no peak, skip it
        if array_pixel_indexes[idx_pix, 0] == -1:
            continue

        spectrum = array_spectra[:, array_pixel_indexes[idx_pix, 0] : array_pixel_indexes[idx_pix, 1] + 1]

        # first normalize the spectrum of current pixel with respect to its own sum
        # actually useless since array_spectra is normally already normalized by pixel
        spectrum[1, :] /= np.sum(spectrum[1, :])

        # then move spectrum to uncompressed version
        spectrum = convert_array_to_fine_grained(spectrum, 10 ** -3, lb=350, hb=1250)

        # then normalize with respect to all pixels
        spectrum[1, :] /= spectrum_sum[1, :]

        # then back to original space
        spectrum = strip_zeros(spectrum)

        # store back the spectrum
        if spectrum.shape[1] == array_pixel_indexes[idx_pix, 1] + 1 - array_pixel_indexes[idx_pix, 0]:
            array_spectra_normalized[
                :, array_pixel_indexes[idx_pix, 0] : array_pixel_indexes[idx_pix, 1] + 1
            ] = spectrum
        else:
            # store shorter-sized spectrum in array_spectra_normalized, rest will be zeros
            array_spectra_normalized[
                :, array_pixel_indexes[idx_pix, 0] : array_pixel_indexes[idx_pix, 0] + len(spectrum) + 1
            ]

    return array_spectra_normalized


# Get image between two mz value
@jit(nopython=True)
def return_image_using_index_lookup(
    low_bound,
    high_bound,
    array_spectra,
    array_pixel_indexes,
    img_shape,
    lookup_table_spectra,
    divider_lookup,
    normalize,
):
    image = np.zeros((img_shape[0], img_shape[1]), dtype=np.float32)
    # Find lower bound and add from there
    for idx_pix in range(array_pixel_indexes.shape[0]):

        # If pixel contains no peak, skip it
        if array_pixel_indexes[idx_pix, 0] == -1:
            continue

        # normalize the spectrum with respect to its sum (for each pixel separately)
        # NB: since the spectra are already normalized, this parameter shouldn't change anything
        if normalize:
            norm_factor = np.sum(
                array_spectra[1, array_pixel_indexes[idx_pix, 0] : array_pixel_indexes[idx_pix, 1] + 1]
            )
        else:
            norm_factor = 1.0

        # sum the mz values over the desired range
        lower_bound = lookup_table_spectra[int(low_bound // divider_lookup)][idx_pix]
        higher_bound = lookup_table_spectra[int(np.ceil(high_bound / divider_lookup))][idx_pix]  # TO CHECK

        """
        higher_bound = array_pixel_indexes[idx_pix, 1]
        for i in range(lower_bound, higher_bound + 1):
            if array_spectra[0, i] > high_bound:
                break

            if array_spectra[0, i] >= low_bound:
                image[convert_spectrum_idx_to_coor(idx_pix, img_shape)] += array_spectra[1, i] / norm_factor
        """

        array_to_sum = array_spectra[:, lower_bound : higher_bound + 1]
        for i in range(0, higher_bound + 1 - lower_bound):
            if array_to_sum[0, i] > high_bound:
                break

            if array_to_sum[0, i] >= low_bound:
                image[convert_spectrum_idx_to_coor(idx_pix, img_shape)] += array_to_sum[1, i] / norm_factor

    return image


@jit(nopython=True)
def return_image_using_index_and_image_lookup(
    low_bound,
    high_bound,
    array_spectra,
    array_pixel_indexes,
    img_shape,
    lookup_table_spectra,
    lookup_table_image,
    divider_lookup,
    normalize,
):

    # Image lookup table is not worth it for small differences between the bound
    if (high_bound - low_bound) < 20:
        return return_image_using_index_lookup(
            low_bound,
            high_bound,
            array_spectra,
            array_pixel_indexes,
            img_shape,
            lookup_table_spectra,
            divider_lookup,
            normalize,
        )
    else:
        image = (
            lookup_table_image[int(high_bound) // divider_lookup]
            - lookup_table_image[int(low_bound) // divider_lookup]
        )
        if normalize:
            # divide by the integral over the whole spectrum
            image /= lookup_table_image[140]

        # Look for true lower bound between the lower looked up image and the next one
        for idx_pix, i in enumerate(lookup_table_spectra[int(low_bound) // divider_lookup]):

            # If pixel contains no peak, skip it
            if array_pixel_indexes[idx_pix, 0] == -1:
                continue

            while array_spectra[0, i] < low_bound and i <= array_pixel_indexes[idx_pix, 1]:

                # If the highest peak is before the lookup value, just skip it altogether
                if array_spectra[0, i] < (int(low_bound) // divider_lookup) * divider_lookup:
                    break

                image[convert_spectrum_idx_to_coor(idx_pix, img_shape)] -= array_spectra[1, i]
                i += 1

        for idx_pix, i in enumerate(lookup_table_spectra[int(high_bound) // divider_lookup]):

            # If pixel contains no peak, skip it
            if array_pixel_indexes[idx_pix, 0] == -1:
                continue

            while array_spectra[0, i] <= high_bound and i <= array_pixel_indexes[idx_pix, 1]:

                # If the highest peak is before the lookup value, just skip it altogether
                if array_spectra[0, i] < (int(high_bound) // divider_lookup) * divider_lookup:
                    break

                image[convert_spectrum_idx_to_coor(idx_pix, img_shape)] += array_spectra[1, i]
                i += 1

        return image


@jit(nopython=True)
def return_index_boundaries_nolookup(low_bound, high_bound, array_mz):
    index_low_bound = 0
    index_high_bound = array_mz.shape[0] - 1

    for i, mz in enumerate(array_mz):
        if mz >= low_bound:
            index_low_bound = i
            break

    for i, mz in enumerate(array_mz[index_low_bound:]):
        if mz > high_bound:
            index_high_bound = i + index_low_bound
            break

    return index_low_bound, index_high_bound


@jit(nopython=True)
def return_index_boundaries(low_bound, high_bound, array_mz, lookup_table):
    index_low_bound = 0
    index_high_bound = array_mz.shape[0] - 1

    for i, mz in enumerate(array_mz[lookup_table[int(low_bound)] :]):
        if mz >= low_bound:
            index_low_bound = i + lookup_table[int(low_bound)]
            break

    for i, mz in enumerate(array_mz[lookup_table[int(high_bound)] :]):
        if mz > high_bound:
            index_high_bound = i + lookup_table[int(high_bound)]
            break

    return index_low_bound, index_high_bound


@jit(nopython=True)
def return_spectrum_per_pixel(idx_pix, array_spectra, array_pixel_indexes):
    idx_1, idx_2 = array_pixel_indexes[idx_pix]
    if idx_1 == -1:
        idx_2 == -2  # To return empty list in the end
    return array_spectra[:, idx_1 : idx_2 + 1]


@jit(nopython=True)
def add_zeros_to_spectrum(array_spectra, pad_individual_peaks=True, padding=10 ** -5):

    # For speed, allocate array of maximum size
    new_array_spectra = np.zeros((array_spectra.shape[0], array_spectra.shape[1] * 3), dtype=np.float32)
    array_index_padding = np.zeros((array_spectra.shape[1]), dtype=np.int32)

    if pad_individual_peaks:
        pad = 0
        for i in range(array_spectra.shape[1] - 1):

            # If there's a discontinuity between two peaks, pad with zeros
            if array_spectra[0, i + 1] - array_spectra[0, i] >= 2 * 10 ** -4:

                # Add left peak
                new_array_spectra[0, i + pad] = array_spectra[0, i]
                new_array_spectra[1, i + pad] = array_spectra[1, i]

                # Add zero to the right of left peak
                pad += 1
                new_array_spectra[0, i + pad] = array_spectra[0, i] + padding
                new_array_spectra[1, i + pad] = 0

                # Add zero to the left of right peak
                pad += 1
                new_array_spectra[0, i + pad] = array_spectra[0, i + 1] - padding
                new_array_spectra[1, i + pad] = 0

                # Right peak added in the next loop iteration

                # Record that 2 zeros have been added between idx i and i+1
                array_index_padding[i] = 2

            else:
                new_array_spectra[0, i + pad] = array_spectra[0, i]
                new_array_spectra[1, i + pad] = array_spectra[1, i]

        new_array_spectra[0, array_spectra.shape[1] + pad - 1] = array_spectra[0, -1]
        new_array_spectra[1, array_spectra.shape[1] + pad - 1] = array_spectra[1, -1]
        return new_array_spectra[:, : array_spectra.shape[1] + pad], array_index_padding

    else:
        for i in range(array_spectra.shape[1]):
            # Store old array in a regular grid in the extended array
            new_array_spectra[0, 3 * i + 1] = array_spectra[0, i]
            new_array_spectra[1, 3 * i + 1] = array_spectra[1, i]

            # Add zeros in the remaining slots
            new_array_spectra[0, 3 * i] = array_spectra[0, i] - padding
            new_array_spectra[0, 3 * i + 2] = array_spectra[0, i] + padding

            array_index_padding[i] = 2

        return new_array_spectra, array_index_padding


@jit(nopython=True)
def return_zeros_extended_spectrum_per_pixel(idx_pix, array_spectra, array_pixel_indexes):
    array_spectra = return_spectrum_per_pixel(idx_pix, array_spectra, array_pixel_indexes)
    new_array_spectra, array_index_padding = add_zeros_to_spectrum(array_spectra)
    return new_array_spectra


@jit(nopython=True)
def reduce_resolution_sorted(array_spectra, resolution=10 ** -3, max_intensity=True):
    """Recompute a sparce representation of the spectrum at a lower (fixed) resolution
       Resolution should be <=10**-4 as it's the maximum precision allowd by float32
    Arguments
    ---------
    array_spectra: np.ndarray, shape=(2, n)
    
    resolution: float
        the size of the bin used to collapse intensities

    max_intensity: bool
        if True, for the new m/z bins return the maximum intensity. Else returns additive intensity
    Returns
    -------
    """
    # First just count the unique values and store them to avoid recalc
    current_mz = -1.0
    cnt = 0
    size_mz_domain = array_spectra.shape[1]
    approx_mz = np.empty(size_mz_domain, dtype=np.float32)
    for i in range(size_mz_domain):
        approx_mz[i] = np.floor(array_spectra[0, i] / resolution) * resolution
        if approx_mz[i] != current_mz:
            cnt += 1
            current_mz = approx_mz[i]

    new_mz = np.empty(cnt, dtype=np.float32)
    new_intensity = np.empty(cnt, dtype=np.float32)

    current_mz = -1.0
    rix = -1
    for i in range(size_mz_domain):
        if approx_mz[i] != current_mz:
            rix += 1
            new_mz[rix] = approx_mz[i]
            new_intensity[rix] = array_spectra[1, i]
            current_mz = approx_mz[i]
        else:
            # Retrieve the maximum intensity value within the new bin
            if max_intensity:
                # Check that the new intensity is greater than what is already there
                if array_spectra[1, i] > new_intensity[rix]:
                    new_intensity[rix] = array_spectra[1, i]

            # Sum the intensity values within the new bin
            else:
                new_intensity[rix] += array_spectra[1, i]

    new_array_spectra = np.empty((2, new_mz.shape[0]), dtype=np.float32)
    new_array_spectra[0, :] = new_mz
    new_array_spectra[1, :] = new_intensity
    return new_array_spectra


@jit(nopython=True)
def compute_spectrum_per_row_selection(
    list_index_bound_rows,
    list_index_bound_column_per_row,
    array_spectra,
    array_pixel_indexes,
    image_shape,
    zeros_extend=True,
    sample=False,
):

    # Compute size array
    size_array = 0
    ll_idx = []
    # This loop should be more or less instantaneous
    for i, x in enumerate(range(list_index_bound_rows[0], list_index_bound_rows[1] + 1)):
        # Careful: list_rows[i] must be even
        l_idx = []

        # Sample only one row out of four
        if sample and i % 4 != 0:
            ll_idx.append(l_idx)
            continue
        else:
            for j in range(0, len(list_index_bound_column_per_row[i]), 2):
                # Check if we're not just looping over zero padding
                if list_index_bound_column_per_row[i][j] == 0 and list_index_bound_column_per_row[i][j + 1] == 0:
                    continue
                idx_pix_1 = convert_coor_to_spectrum_idx((x, list_index_bound_column_per_row[i][j]), image_shape)
                idx_1 = array_pixel_indexes[idx_pix_1, 0]
                idx_pix_2 = convert_coor_to_spectrum_idx((x, list_index_bound_column_per_row[i][j + 1]), image_shape)
                idx_2 = array_pixel_indexes[idx_pix_2, 1]

                # Case we started or finished with empty pixel
                if idx_1 == -1 or idx_2 == -1:
                    j = 1
                    while idx_1 == -1:
                        idx_1 = array_pixel_indexes[idx_pix_1 + j, 0]
                        j += 1

                    j = 1
                    while idx_2 == -1:
                        idx_2 = array_pixel_indexes[idx_pix_2 - j, 1]
                        j += 1

                # Check that we still have idx_2>=idx_1
                if idx_1 > idx_2:
                    pass
                else:
                    size_array += idx_2 + 1 - idx_1
                    l_idx.extend([idx_1, idx_2])

            ll_idx.append(l_idx)

    # Init array selection of size size_array
    array_spectra_selection = np.zeros((2, size_array), dtype=np.float32)
    pad = 0

    # Fill array line by line
    for i, x in enumerate(range(list_index_bound_rows[0], list_index_bound_rows[1] + 1)):
        for idx_1, idx_2 in zip(ll_idx[i][0:-1:2], ll_idx[i][1::2]):
            array_spectra_selection[:, pad : pad + idx_2 + 1 - idx_1] = array_spectra[:, idx_1 : idx_2 + 1]
            pad += idx_2 + 1 - idx_1

    # Sort array
    array_spectra_selection = array_spectra_selection[:, array_spectra_selection[0].argsort()]
    # Iteratively bin at 1e-4 because too many values to display (also sum of the array together in the process)
    array_spectra_selection = reduce_resolution_sorted(array_spectra_selection, 10 ** -4, max_intensity=False)
    # Pad with zeros
    if zeros_extend:
        array_spectra_selection, array_index_padding = add_zeros_to_spectrum(array_spectra_selection)
    return array_spectra_selection


@jit(nopython=True)
def sample_rows_from_path(path):
    # Careful: in this whole function, x is the vertical axis (from top to bottom), and y the horizontal one
    # this is counter-intuitive given the computations done in the function

    x_min = path[:, 0].min()
    x_max = path[:, 0].max()

    # Numba won't accept a list of list, so I have to use a list of np arrays
    list_index_bound_column_per_row = [np.arange(0) for x in range(x_min, x_max + 1)]
    dir_prev = None

    for i in range(path.shape[0] - 1):
        x1, y1 = path[i]
        x2, y2 = path[i + 1]
        if x2 != x1:
            slope = (y2 - y1) / (x2 - x1)
            intercept = y1 - slope * x1

            # Compute if change of direction on the x-axis and correct accordingly
            if x2 >= x1:
                dir = 1
            else:
                dir = -1
            if dir_prev is None or dir == dir_prev:
                offset = 0
            else:
                offset = dir
            dir_prev = dir

            # For each x, get the corresponding y (with non constant sampling on y axis)
            for x in range(x1 + offset, x2, dir):
                list_index_bound_column_per_row[x - x_min] = np.append(
                    list_index_bound_column_per_row[x - x_min], round(slope * x + intercept)
                )

    # Min x and max x often cover only zero or one pixel due to the way the sampling is done, we just get rid of them
    if len(list_index_bound_column_per_row[0]) < 2:
        del list_index_bound_column_per_row[0]
        x_min += 1
    if len(list_index_bound_column_per_row[-1]) < 2:
        del list_index_bound_column_per_row[-1]
        x_max -= 1

    # Clean list
    l_to_del = []
    for x in range(x_min, x_max + 1):

        # If everything went fine, x should appear an even number of times
        if len(list_index_bound_column_per_row[x - x_min]) % 2 == 0:
            pass
        else:
            print("BUG WITH LIST X", x, list_index_bound_column_per_row[x - x_min])
            if (
                len(list_index_bound_column_per_row[x - x_min]) % 2 == 1
                and len(list_index_bound_column_per_row[x - x_min]) != 1
            ):
                list_index_bound_column_per_row[x - x_min] = list_index_bound_column_per_row[x - x_min][:-1]
            else:
                list_index_bound_column_per_row[x - x_min] = np.append(
                    list_index_bound_column_per_row[x - x_min], list_index_bound_column_per_row[x - x_min][0]
                )
        list_index_bound_column_per_row[x - x_min].sort()  # Inplace sort

    # Convert list of np.array to np array padded with zeros (for numba compatibility...)
    max_len = max([len(i) for i in list_index_bound_column_per_row])
    array_index_bound_column_per_row = np.zeros((len(list_index_bound_column_per_row), max_len), dtype=np.int32)
    for i, arr in enumerate(list_index_bound_column_per_row):
        array_index_bound_column_per_row[i, : len(arr)] = arr

    return np.array([x_min, x_max], dtype=np.int32), array_index_bound_column_per_row


# This function returns the corresponding lipid name from a list of m/z values. l_min and l_max correspond to the peak
# boundaries of the identified lipids zero padding extra is needed for both taking into account the zero-padding
# (this way zeros on the sides of the peak are also identified as the annotated lipid) but also because the annotation
# is very stringent in the first place, and sometimes border of the peaks are missing in the annotation
@jit(nopython=True)
def return_index_labels(l_min, l_max, l_mz, zero_padding_extra=5 * 10 ** -5):

    # Build empty array for lipid indexes
    array_indexes = np.empty((len(l_mz),), dtype=np.int32)
    array_indexes.fill(-1)
    idx_lipid = 0
    idx_mz = 0
    while idx_lipid < len(l_min) and idx_mz < len(l_mz):

        # Case peak is in lipid boundaries
        if (
            l_mz[idx_mz] >= l_min[idx_lipid] - zero_padding_extra
            and l_mz[idx_mz] <= l_max[idx_lipid] + zero_padding_extra
        ):
            array_indexes[idx_mz] = idx_lipid
            idx_mz += 1

        # Case peak is before lipid boundaries
        elif l_mz[idx_mz] < l_min[idx_lipid] - zero_padding_extra:
            # array_indexes[idx_mz] = -1
            idx_mz += 1

        # Case peak is after lipid boundaries
        elif l_mz[idx_mz] > l_max[idx_lipid] + zero_padding_extra:
            idx_lipid += 1

    return array_indexes


@jit(nopython=True)
def return_avg_intensity_per_lipid(l_intensity_with_lipids, l_idx_labels):
    l_unique_idx_labels = []
    l_avg_intensity = []
    idx_label_temp = -1
    for i, idx_label in enumerate(l_idx_labels):

        # Actual lipid and not just a placeholder
        if idx_label >= 0:

            # New lipid is discovered
            if idx_label != idx_label_temp:
                idx_label_temp = l_idx_labels[i]
                l_avg_intensity.append(l_intensity_with_lipids[i])
                l_unique_idx_labels.append(idx_label)

            # Continuity of the previous lipid
            else:
                l_avg_intensity[-1] += l_intensity_with_lipids[i]

    return l_unique_idx_labels, l_avg_intensity


@jit(nopython=True)
def project_image(index_slice, original_image, array_projection_correspondence):
    # correct index
    index_slice -= 1

    new_image = np.zeros(array_projection_correspondence.shape[1:-1], dtype=original_image.dtype)
    # exclude the borders of the image to gain some time
    for i in range(50, array_projection_correspondence[index_slice].shape[0] - 50):
        for j in range(50, array_projection_correspondence[index_slice].shape[1] - 50):
            # coordinate -1 corresponds to unassigned
            if array_projection_correspondence[index_slice, i, j, 0] != -1:
                x, y = array_projection_correspondence[index_slice, i, j]
                new_image[i, j] = original_image[x, y]

    return new_image


@jit(nopython=True)
def get_projected_atlas_mask(stack_mask, slice_coordinates, shape_atlas):

    projected_mask = np.full(slice_coordinates.shape[:-1], stack_mask[0, 0, 0], dtype=np.int32)
    for x in range(slice_coordinates.shape[0]):
        for y in range(slice_coordinates.shape[1]):
            current_coor_rescaled = slice_coordinates[x, y]
            if (
                min(current_coor_rescaled) >= 0
                and current_coor_rescaled[0] < shape_atlas[0]
                and current_coor_rescaled[1] < shape_atlas[1]
                and current_coor_rescaled[2] < shape_atlas[2]
            ):
                projected_mask[x, y] = stack_mask[
                    current_coor_rescaled[0], current_coor_rescaled[1], current_coor_rescaled[2]
                ]
    return projected_mask


@jit(nopython=True)
def get_array_rows_from_atlas_mask(mask, mask_remapped, array_projection_correspondence):
    # map back the mask coordinates to original data
    for x in range(mask.shape[0]):
        for y in range(mask.shape[1]):
            x_original, y_original = array_projection_correspondence[x, y]
            if (
                x_original >= 0
                and x_original < mask_remapped.shape[0]
                and y_original >= 0
                and y_original < mask_remapped.shape[0]
            ):
                mask_remapped[x_original, y_original] = mask[x, y]

    # then compute the rows
    ll_rows = []
    for x in range(mask_remapped.shape[0]):
        first = False
        ymin = -1
        ymax = -1
        l_rows = [x]
        for y in range(mask_remapped.shape[1]):
            if mask_remapped[x, y] != 0 and not first:
                ymin = y
                first = True
            elif mask_remapped[x, y] == 0 and first:

                # correct for bug due to mask assignment with different resolution
                if np.max(mask_remapped[x, y : y + 5]) != 0:
                    continue
                else:
                    ymax = y
                    first = False
                    l_rows.extend([ymin, ymax - 1])
        if len(l_rows) > 1:
            ll_rows.append(l_rows)

    if len(ll_rows) > 0:
        xmin = ll_rows[0][0]
        xmax = ll_rows[-1][0]
        max_len = max([len(l_rows) - 1 for l_rows in ll_rows])
    else:
        xmax = 0
        xmin = 0
        max_len = 0
    # Convert list of np.array to np array padded with zeros (for numba compatibility...)
    array_index_bound_column_per_row = np.zeros((xmax - xmin + 1, max_len), dtype=np.int32)
    for i, l_rows in enumerate(ll_rows):
        array_index_bound_column_per_row[i, : len(l_rows) - 1] = l_rows[1:]

    return np.array([xmin, xmax], dtype=np.int32), array_index_bound_column_per_row


@jit(nopython=True)
def convert_array_to_fine_grained(array, resolution, lb=350, hb=1250):
    # this function converts a compressed sparse array into the uncompressed version.
    # If several values of the compressed version map to the same value of the uncompressed one, they are added
    # Therefore, when ran on the spectrum of a whole image, it add the spectra of all pixels
    new_array = np.linspace(lb, hb, int(round((hb - lb) * resolution ** -1)))
    new_array = np.vstack((new_array, np.zeros(new_array.shape, dtype=np.float32)))
    for mz, intensity in array.T:
        new_array[1, int(round((mz - lb) * (1 / resolution)))] += intensity

    return new_array


@jit(nopython=True)
def strip_zeros(array):
    l_to_keep = [idx for idx, x in enumerate(array[1, :]) if x != 0 and not np.isnan(x)]
    array_mz = array[0, :].take(l_to_keep)
    array_intensity = array[1, :].take(l_to_keep)
    return np.vstack((array_mz, array_intensity))

