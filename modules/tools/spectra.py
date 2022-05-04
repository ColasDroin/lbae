# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" In this module, functions used to handle the MALDI data (e.g. get all pixels values for a given 
lipid annotation, for of a given slice) are defined.
"""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import time
import numpy as np
from numba import njit, jit
import logging

# mspec module
from modules.tools.external_lib.mspec import reduce_resolution_sorted

# ==================================================================================================
# --- Functions for coordinates indices manipulation
# ==================================================================================================
@njit
def convert_spectrum_idx_to_coor(index, shape):
    """This function takes a pixel index and converts it into a tuple of integers representing the
    coordinates of the pixel in the current slice.

    Args:
        index (int): Pixel index in a flattened version of the slice image.
        shape (tuple(int)): Shape of the MALDI acquisition of the corresponding slice.

    Returns:
        tuple(int): Corresponding coordinate in the original image.
    """
    return int(index / shape[1]), int(index % shape[1])


@njit
def convert_coor_to_spectrum_idx(coordinate, shape):
    """This function takes a tuple of integers representing the coordinates of the pixel in the
    current slice and converts it into an index in a flattened version of the image.

    Args:
        coordinate tuple(int): Coordinate in the original image.
        shape (tuple(int)): Shape of the MALDI acquisition of the corresponding slice.

    Returns:
        int: Pixel index in a flattened version of the slice image.
    """
    ind = coordinate[0] * shape[1] + coordinate[1]
    if ind >= shape[0] * shape[1]:
        # logging.warning("Index not allowed.")
        return -1
    return ind


# ==================================================================================================
# --- Functions to normalize spectrum
# ==================================================================================================


@njit
def compute_normalized_spectra(array_spectra, array_pixel_indexes):
    """This function takes an array of spectra and returns it normalized (per pixel). In pratice,
    each pixel spectrum is converted into a uncompressed version, and divided by the sum of all
    spectra. This might a problematic approach as there seems to be small shifts between spectra
    across pixels, leading to a noise amplification after normalization.

    Args:
        array_spectra (np.ndarray): An array of shape (2,n) containing spectrum
            data (m/z and intensity) for each pixel.
        array_pixel_indexes (np.ndarray): An array of shape (m,2) containing the boundary indices of
            each pixel in array_spectra.

    Returns:
        (np.ndarray): An array of shape (2,m) containing the normalized spectrum data (m/z and
            intensity).
    """
    # Start by converting array_spectra into a very fine-grained version
    spectrum_sum = convert_array_to_fine_grained(array_spectra, 10**-3, lb=350, hb=1250) + 1
    array_spectra_normalized = np.zeros(array_spectra.shape, dtype=np.float32)

    # Loop over the spectrum of each pixel
    for idx_pix in range(array_pixel_indexes.shape[0]):
        logging.info(
            "_compute_normalized_spectra:"
            + str(idx_pix / array_pixel_indexes.shape[0] * 100)
            + " done"
        )

        # If pixel contains no peak, skip it
        if array_pixel_indexes[idx_pix, 0] == -1:
            continue

        # Get the spectrum of current pixel
        spectrum = array_spectra[
            :, array_pixel_indexes[idx_pix, 0] : array_pixel_indexes[idx_pix, 1] + 1
        ]

        # Out of safety, normalize the spectrum of current pixel with respect to its own sum
        # Might be useless since array_spectra is normally already normalized by pixel
        spectrum[1, :] /= np.sum(spectrum[1, :])

        # Then move spectrum to uncompressed version
        spectrum = convert_array_to_fine_grained(spectrum, 10**-3, lb=350, hb=1250)

        # Then normalize with respect to all pixels
        spectrum[1, :] /= spectrum_sum[1, :]

        # Then back to original space
        spectrum = strip_zeros(spectrum)

        # Store back the spectrum
        if (
            spectrum.shape[1]
            == array_pixel_indexes[idx_pix, 1] + 1 - array_pixel_indexes[idx_pix, 0]
        ):
            array_spectra_normalized[
                :, array_pixel_indexes[idx_pix, 0] : array_pixel_indexes[idx_pix, 1] + 1
            ] = spectrum
        else:
            # Store shorter-sized spectrum in array_spectra_normalized, rest will be zeros
            array_spectra_normalized[
                :,
                array_pixel_indexes[idx_pix, 0] : array_pixel_indexes[idx_pix, 0]
                + len(spectrum)
                + 1,
            ]

    return array_spectra_normalized


@njit
def convert_array_to_fine_grained(array, resolution, lb=350, hb=1250):
    """This function converts an array to a fine-grained version, which is common to all pixels,
    allowing for easier computations. If several values of the compressed version map to the same
    value of the uncompressed one, they are summed. Therefore, when ran on the spectrum of a whole
    image, it adds the spectra of all pixels.

    Args:
        array (np.ndarray): An array of shape (2,n) containing spectrum data (m/z
            and intensity).
        resolution (float): The resolution used for finer-graining.
        lb (int, optional): Lower bound for the fine-grained array. Defaults to 350.
        hb (int, optional): Higher bound for the fine-grained array. Defaults to 1250.

    Returns:
        np.ndarray: A sparse, fine-grained array of shape (2,m) containing spectrum data (m/z and
        intensity).
    """
    # Build an empty (zeroed) array with the requested uncompressed size
    new_array = np.linspace(lb, hb, int(round((hb - lb) * resolution**-1)))
    new_array = np.vstack((new_array, np.zeros(new_array.shape, dtype=np.float32)))

    # Fill it with the values from the compressed array
    for mz, intensity in array.T:
        new_array[1, int(round((mz - lb) * (1 / resolution)))] += intensity

    return new_array


@njit
def strip_zeros(array):
    """This function strips a (potentially sparse) array (e.g. one that has been converted with
    convert_array_to_fine_grained) from its columns having intensity zero.

    Args:
        array (np.ndarray): An array of shape (2,n) containing spectrum data (m/z
            and intensity).

    Returns:
        np.ndarray: The same array stripped from its zero intensity values. Now of shape (2,m).
    """
    # Look for the non-zero values and store them in l_to_keep
    l_to_keep = [idx for idx, x in enumerate(array[1, :]) if x != 0 and not np.isnan(x)]

    # Keep only the previsouly assigned non-zero values
    array_mz = array[0, :].take(l_to_keep)
    array_intensity = array[1, :].take(l_to_keep)
    return np.vstack((array_mz, array_intensity))


# ==================================================================================================
# --- Functions to compute image from lipid selection
# ==================================================================================================


@jit
def compute_image_using_index_lookup(
    low_bound,
    high_bound,
    array_spectra,
    array_pixel_indexes,
    img_shape,
    lookup_table_spectra,
    divider_lookup,
    array_peaks_transformed_lipids,
    array_corrective_factors,
    apply_transform,
):
    """For each pixel, this function extracts from array_spectra the intensity of a given m/z
    selection (normally corresponding to a lipid annotation) defined by a lower and a higher bound.
    For faster computation, it uses lookup_table_spectra to map m/z values to given indices. It then
    assigns the pixel intensity to an array of shape img_shape, therefore producing an image
    representing the requested lipid distribution.

    Args:
        low_bound (float): Lower m/z value for the annotation.
        high_bound (float): Higher m/z value for the annotation.
        array_spectra (np.ndarray): An array of shape (2,n) containing spectrum data (m/z and
            intensity) for each pixel.
        array_pixel_indexes (np.ndarray): An array of shape (m,2) containing the boundary indices of
            each pixel in array_spectra.
        img_shape (tuple(int)): A tuple with the two integer values corresponding to height and
            width of the current slice acquisition.
        lookup_table_spectra (np.ndarray): An array of shape (k,m) representing a lookup table with
            the following mapping: lookup_table_spectra[i,j] contains the first m/z index of pixel
            j such that m/z >= i * divider_lookup.
        divider_lookup (int): Integer used to set the resolution when building the lookup table.
        array_peaks_transformed_lipids (np.ndarray): A two-dimensional numpy array, which contains
            the peak annotations (min peak, max peak, average value of the peak), sorted by min_mz,
            for the lipids that have been transformed.
        array_corrective_factors (np.ndarray): A three-dimensional numpy array, which contains the
            MAIA corrective factor used for lipid (first dimension) and each pixel (second and third
            dimension).
        apply_transform (bool): If True, the MAIA correction for pixel intensity is reverted.

    Returns:
        np.ndarray: An array of shape img_shape (reprensenting an image) containing the cumulated
            intensity of the spectra between low_bound and high_bound, for each pixel.
    """
    # Build empty image
    image = np.zeros((img_shape[0], img_shape[1]), dtype=np.float32)

    # Build an array of ones for the correction (i.e. default is no correction)
    array_corrective_factors_lipid = np.ones((img_shape[0] * img_shape[1],), np.float32)

    if apply_transform:
        # Check if the m/z region must transformed, i.e. low and high bound are inside annotation
        idx_lipid_right = -1
        for idx_lipid, (min_mz, max_mz, avg_mz) in enumerate(array_peaks_transformed_lipids):
            # Take 10**-4 for precision
            if (low_bound + 10**-4) >= min_mz and (high_bound - 10**-4) <= max_mz:
                idx_lipid_right = idx_lipid
                break

        # If the current region corresponds to a transformed lipid:
        if idx_lipid_right != -1:
            array_corrective_factors_lipid[:] = array_corrective_factors[idx_lipid_right].flatten()

    # Find lower bound and add from there
    for idx_pix in range(array_pixel_indexes.shape[0]):

        # If pixel contains no peak, skip it
        if array_pixel_indexes[idx_pix, 0] == -1:
            continue

        # Compute range in which values must be summed and extract corresponding part of spectrum
        lower_bound = lookup_table_spectra[int(low_bound / divider_lookup)][idx_pix]
        higher_bound = lookup_table_spectra[int(np.ceil(high_bound / divider_lookup))][idx_pix]
        array_to_sum = array_spectra[:, lower_bound : higher_bound + 1]

        # Apply MAIA correction
        if array_corrective_factors_lipid[idx_pix] == 0:
            correction = 1.0
        else:
            correction = array_corrective_factors_lipid[idx_pix]

        # Sum the m/z values over the requested range
        image = _fill_image(
            image,
            idx_pix,
            img_shape,
            array_to_sum,
            lower_bound,
            higher_bound,
            low_bound,
            high_bound,
            correction,
        )

    return image


@njit
def _fill_image(
    image,
    idx_pix,
    img_shape,
    array_to_sum,
    lower_bound,
    higher_bound,
    low_bound,
    high_bound,
    correction,
):
    """This internal function is used to fill the image provided as an argument with the
    intensities corresponding to the selection between low and high bounds."""
    # While i is in the interval of the current lipid annotation, delimited by low and high bounds,
    # fill image with intensities
    for i in range(0, higher_bound + 1 - lower_bound):

        # If i corresponds to a m/z value above the high_bound of the lipid annotation, exit loop
        if array_to_sum[0, i] > high_bound:
            break

        # If i is in the interval of the lipid annotation, keep filling the image
        if array_to_sum[0, i] >= low_bound:
            image[convert_spectrum_idx_to_coor(idx_pix, img_shape)] += (
                array_to_sum[1, i] * correction
            )
    return image


def compute_image_using_index_and_image_lookup(
    low_bound,
    high_bound,
    array_spectra,
    array_pixel_indexes,
    img_shape,
    lookup_table_spectra,
    lookup_table_image,
    divider_lookup,
    array_peaks_transformed_lipids,
    array_corrective_factors,
    apply_transform=False,
):
    """This function is very much similar to compute_image_using_index_lookup, except that it uses a
    different lookup table: lookup_table_image. This lookup table contains the cumulated intensities
    above the current lookup (instead of the sheer intensities). Therefore, any image corresponding
    to the integral of all pixel spectra between two bounds can be approximated by the difference of
    the lookups closest to these bounds. The integral can then be corrected a posteriori to obtain
    the exact value. If the m/z distance between the two bounds is low, it calls
    compute_image_using_index_lookup() as the optimization is not worth it. It wraps the internal
    functions _compute_image_using_index_and_image_lookup_full() and
    _compute_image_using_index_and_image_lookup_partial() to ensure that the proper array type is
    used with numba.

    Args:
        low_bound (float): Lower m/z value for the annotation.
        high_bound (float): Higher m/z value for the annotation.
        array_spectra (np.ndarray): An array of shape (2,n) containing spectrum
            data (m/z and intensity) for each pixel.
        array_pixel_indexes (np.ndarray): An array of shape (m,2) containing the boundary indices of
            each pixel in array_spectra.
        img_shape (tuple(int)): A tuple with the two integer values corresponding to height and
        width of the current slice acquisition.
        lookup_table_spectra (np.ndarray): An array of shape (k,m) representing a
            lookup table with the following mapping: lookup_table_spectra[i,j] contains the first
            m/z index of pixel j such that m/z >= i * divider_lookup.
        lookup_table_image (np.ndarray): An array of shape (k,m) representing a
            lookup table with the following mapping: lookup_table_image[i,j] contains, for the pixel
            of index j, the cumulated intensities from the lowest possible m/z until the first m/z
            such that m/z >= i * divider_lookup.
        divider_lookup (int): Integer used to set the resolution when building the lookup table.
        array_peaks_transformed_lipids (np.ndarray): A two-dimensional numpy array, which contains
            the peak annotations (min peak, max peak, average value of the peak), sorted by min_mz,
            for the lipids that have been transformed.
        array_corrective_factors (np.ndarray): A three-dimensional numpy array, which contains the
            MAIA corrective factor used for lipid (first dimension) and each pixel (second and third
            dimension).
        apply_transform (bool): If True, the MAIA correction for pixel intensity is applied.
            Defaults to False.

    Returns:
        np.ndarray: An array of shape img_shape (reprensenting an image) containing the cumulated
            intensity of the spectra between low_bound and high_bound, for each pixel.
    """

    # Image lookup table is not worth it for small differences between the bounds
    # And image lookup can't be used if the transformation should not be applied
    if (high_bound - low_bound) < 5 or apply_transform:
        return compute_image_using_index_lookup(
            low_bound,
            high_bound,
            array_spectra,
            array_pixel_indexes,
            img_shape,
            lookup_table_spectra,
            divider_lookup,
            array_peaks_transformed_lipids,
            array_corrective_factors,
            apply_transform,
        )

    else:
        return _compute_image_using_index_and_image_lookup_partial(
            low_bound,
            high_bound,
            array_spectra,
            array_pixel_indexes,
            img_shape,
            lookup_table_spectra,
            lookup_table_image,
            divider_lookup,
        )


@njit
def _compute_image_using_index_and_image_lookup_partial(
    low_bound,
    high_bound,
    array_spectra,
    array_pixel_indexes,
    img_shape,
    lookup_table_spectra,
    lookup_table_image,
    divider_lookup,
):
    """This internal function is wrapped by compute_image_using_index_and_image_lookup(). It is used
    as a slower, memory-optimized, option, when the slice data must be manually extracted from a
    memory-mapped array. Please consult the documentation of
    compute_image_using_index_and_image_lookup() for more information.
    """
    # Get a first approximate of the requested lipid image
    image = (
        lookup_table_image[int(high_bound / divider_lookup)]
        - lookup_table_image[int(low_bound / divider_lookup)]
    )  # Normalization should be useless here as the spectrum is already normalized

    # Look for true lower/higher bound between the lower/higher looked up image and the next one
    array_idx_low_bound_inf_pix = lookup_table_spectra[int(low_bound / divider_lookup)]
    array_idx_low_bound_sup_pix = lookup_table_spectra[int(np.ceil(low_bound / divider_lookup))]
    array_idx_high_bound_inf_pix = lookup_table_spectra[int(high_bound / divider_lookup)]
    array_idx_high_bound_sup_pix = lookup_table_spectra[int(np.ceil(high_bound / divider_lookup))]
    for (
        idx_pix,
        (idx_low_bound_inf, idx_low_bound_sup, idx_high_bound_inf, idx_high_bound_sup),
    ) in enumerate(
        zip(
            array_idx_low_bound_inf_pix,
            array_idx_low_bound_sup_pix,
            array_idx_high_bound_inf_pix,
            array_idx_high_bound_sup_pix,
        )
    ):

        # Extract array from mmap
        array_to_sum_lb = array_spectra[:, idx_low_bound_inf : idx_low_bound_sup + 1]
        array_to_sum_hb = array_spectra[:, idx_high_bound_inf : idx_high_bound_sup + 1]

        # If pixel contains no peak, skip it
        if array_pixel_indexes[idx_pix, 0] == -1:
            continue

        # Correct the image coming from lookup
        image = _correct_image(
            image,
            idx_pix,
            img_shape,
            array_to_sum_lb,
            array_to_sum_hb,
            low_bound,
            high_bound,
            divider_lookup,
        )

    return image


@njit
def _correct_image(
    image,
    idx_pix,
    img_shape,
    array_to_sum_lb,
    array_to_sum_hb,
    low_bound,
    high_bound,
    divider_lookup,
):
    """This internal function is used to correct the intensities in the image provided as an
    argument, by adding (removing) the intensities that should (not) have been in the selection
    between low and high bounds."""
    # First correct for the m/z values that have been summed in the image and shouldn't have
    i = 0
    while array_to_sum_lb[0, i] < low_bound and i < array_to_sum_lb.shape[1]:

        # If the peak corresponding to highest mz is before the lookup value, just skip it
        # altogether as no correction is needed (empty spectrum between lower and low bound)
        if array_to_sum_lb[0, i] < int(low_bound / divider_lookup) * divider_lookup:
            break

        # Remove intensities that should not have been added in the first place
        image[convert_spectrum_idx_to_coor(idx_pix, img_shape)] -= array_to_sum_lb[1, i]
        i += 1

    # Then add the m/z values that are missing in the image
    i = 0
    while array_to_sum_hb[0, i] <= high_bound and i <= array_to_sum_hb.shape[1]:

        # If the peak corresponding to the highest mz is before the lookup value, just skip it
        # altogether as no correction is needed (empty spectrum between high and higher bound)
        if array_to_sum_hb[0, i] < int(high_bound / divider_lookup) * divider_lookup:
            break

        # Add the missing intensities
        image[convert_spectrum_idx_to_coor(idx_pix, img_shape)] += array_to_sum_hb[1, i]
        i += 1
    return image


def compute_normalized_image_per_lipid(
    lb_mz,
    hb_mz,
    array_spectra,
    array_pixel_indexes,
    image_shape,
    lookup_table_spectra,
    cumulated_image_lookup_table,
    divider_lookup,
    array_peaks_transformed_lipids,
    array_corrective_factors,
    apply_transform=False,
    percentile_normalization=99,
    RGB_channel_format=True,
):
    """This function is mostly a wrapper for compute_image_using_index_and_image_lookup, that is, it
    computes an image containing the cumulated intensity of the spectra between low_bound and
    high_bound, for each pixel. In addition, it adds a step of normalization, such that the output
    is more visually pleasing and comparable across selections. The output can also be provided in
    8 bits, that is, the format of a single channel in a RGB image.

    Args:
        low_bound (float): Lower m/z value for the annotation.
        high_bound (float): Higher m/z value for the annotation.
        array_spectra (np.ndarray): An array of shape (2,n) containing spectrum
            data (m/z and intensity) for each pixel.
        array_pixel_indexes (np.ndarray): An array of shape (m,2) containing the boundary indices of
            each pixel in array_spectra.
        img_shape (tuple(int)): A tuple with the two integer values corresponding to height and
            width of the current slice acquisition.
        lookup_table_spectra (np.ndarray): An array of shape (k,m) representing a
            lookup table with the following mapping: lookup_table_spectra[i,j] contains the first
            m/z index of pixel j such that m/z >= i * divider_lookup.
        lookup_table_image (np.ndarray): An array of shape (k,m) representing a
            lookup table with the following mapping: lookup_table_image[i,j] contains, for the pixel
            of index j, the cumulated intensities from the lowest possible m/z until the first m/z
            such that m/z >= i * divider_lookup.
        divider_lookup (int): Integer used to set the resolution when building the lookup table.
        array_peaks_transformed_lipids (np.ndarray): A two-dimensional numpy array, which contains
            the peak annotations (min peak, max peak, average value of the peak), sorted by min_mz,
            for the lipids that have been transformed.
        array_corrective_factors (np.ndarray): A three-dimensional numpy array, which contains the
            MAIA corrective factor used for lipid (first dimension) and each pixel (second and third
            dimension).
        apply_transform (bool): If True, the MAIA correction for pixel intensity is applied.
            Defaults to False.
        percentile_normalization (int): Integer used to re-normalize the data, such that the maximum
            value correspond to the given percentile.
        RGB_channel_format (bool): If False, the output image is provided as an array with values
            between 0 and 1. Else, the values are between 0 and 255.

    Returns:
        np.ndarray: An array of shape img_shape (reprensenting an image) containing the cumulated
            intensity of the spectra between low_bound and high_bound, for each pixel. This image is
            normalized according to percentile_normalized. Output values are between 0 and 1 (255)
            depending if RGB_channel_format is False (True).
    """
    # Get image from raw mass spec data
    image = compute_image_using_index_and_image_lookup(
        lb_mz,
        hb_mz,
        array_spectra,
        array_pixel_indexes,
        image_shape,
        lookup_table_spectra,
        cumulated_image_lookup_table,
        divider_lookup,
        array_peaks_transformed_lipids,
        array_corrective_factors,
        apply_transform,
    )

    # Normalize by percentile
    image = image / np.percentile(image, percentile_normalization) * 1
    image = np.clip(0, 1, image)

    # Convert image to have values between 0 and 255
    if RGB_channel_format:
        image *= 255
    return image


# ==================================================================================================
# --- Functions to compute m/z boundaries for averaged arrays (1-D lookup table)
# ==================================================================================================
@njit
def compute_index_boundaries_nolookup(low_bound, high_bound, array_spectra_avg):
    """This function computes, from array_spectra_avg, the first existing indices corresponding to
    m/z values above the provided lower and higher bounds, without using any lookup. If high_bound
    and/or low_bound are above the highest possible value for the required lookup, it returns the
    index of the highest existing value. Note that array_spectra_avg normally corresponds to the
    high-resolution spectrum averaged across all pixels, but in can be any spectrum so long as it is
    not subdivided in pixels.

    Args:
        low_bound (float): Lower m/z value for the annotation.
        high_bound (float): Higher m/z value for the annotation.
        array_spectra_avg (np.ndarray): An array of shape (2,n) containing
            spectrum data (m/z and intensity).

    Returns:
        tuple(int): A tuple of integer representing the best guess for the indices of low_bound and
            high_bound in array_spectra_avg.
    """
    # Extract the mz values for array_spectra_avg
    array_mz = array_spectra_avg[0, :]

    # Define intial guess for the low and high bounds indices
    index_low_bound = 0
    index_high_bound = array_mz.shape[0] - 1

    # Browse array_mz until low bound is crossed
    for i, mz in enumerate(array_mz):
        index_low_bound = i
        if mz >= low_bound:
            break

    # Start from the low bound index, and browse array_mz until high bound is crossed
    for i, mz in enumerate(array_mz[index_low_bound:]):
        index_high_bound = i + index_low_bound
        if mz >= high_bound:
            break

    return index_low_bound, index_high_bound


@njit
def compute_index_boundaries(low_bound, high_bound, array_spectra_avg, lookup_table):
    """This function is very much similar to compute_index_boundaries_nolookup(), except that it
    uses lookup_table to find the low and high bounds indices faster. As in
    compute_index_boundaries_nolookup(), it computes, from array_spectra_avg, the first existing
    indices corresponding to m/z values above the provided lower and higher bounds. If high_bound
    and/or low_bound are above the highest possible value for the required lookup, it returns the
    index of the highest existing value. Note that array_spectra_avg normally corresponds to the
    high-resolution spectrum averaged across all pixels, but in can be any spectrum so long as it is
    not subdivided in pixels. Also note that there are no partial full versions of this function
    depending if the dataset is stored in RAM or HDF5, since the two versions would have been almost
    identical (there's no loop over pixels, contrarily to e.g. compute_image_using_index_lookup(),
    and a view/copy of the partial spectra in the selection is made as a first step, turning an in
    a np.ndarray). It wraps the internal numba-ized function _compute_index_boundaries_nolookup().

    Args:
        low_bound (float): Lower m/z value for the annotation.
        high_bound (float): Higher m/z value for the annotation.
        array_spectra_avg (np.ndarray): An array of shape (2,n) containing
            spectrum data (m/z and intensity).
        lookup_table (np.ndarray): A 1-dimensional array of length m providing, for each index (i.e.
            lookup), the index of the first m/z value in the averaged array_spectra superior or
            equal to the lookup.

    Returns:
        tuple(int): A tuple of integer representing the best guess for the indices of low_bound and
        high_bound in array_spectra_avg.
    """
    # Extract the arrays provided by the lookup table as first guess for the low and high bounds
    array_to_sum_lb = array_spectra_avg[
        0, lookup_table[int(low_bound)] : lookup_table[int(np.ceil(low_bound))] + 1
    ]
    array_to_sum_hb = array_spectra_avg[
        0, lookup_table[int(high_bound)] : lookup_table[int(np.ceil(high_bound))] + 1
    ]

    # Correct the lookup indices with these arrays
    return _loop_compute_index_boundaries(
        array_to_sum_lb, array_to_sum_hb, low_bound, high_bound, lookup_table
    )


@njit
def _loop_compute_index_boundaries(
    array_to_sum_lb, array_to_sum_hb, low_bound, high_bound, lookup_table
):
    """This internal function is wrapped by compute_index_boundaries(). Please consult the
    corresponding documentation.
    """
    # Define intial guess for the low and high bounds indices
    index_low_bound = 0
    index_high_bound = lookup_table[int(high_bound)] + array_to_sum_hb.shape[0]

    # Browse array_to_sum_lb until low bound is crossed
    for i, mz in enumerate(array_to_sum_lb):
        index_low_bound = i + lookup_table[int(low_bound)]
        if mz >= low_bound:
            break

    # Browse array_to_sum_hb until high bound is crossed
    for i, mz in enumerate(array_to_sum_hb):
        index_high_bound = i + lookup_table[int(high_bound)]
        if mz >= high_bound:
            break

    return index_low_bound, index_high_bound


# ==================================================================================================
# --- Functions to compute spectra averaged from a manual selection or a mask selection
# ==================================================================================================


@njit
def return_spectrum_per_pixel(idx_pix, array_spectra, array_pixel_indexes):
    """This function returns the spectrum of the pixel having index pixel_idx, using the lookup
    table array_pixel_indexes.

    Args:
        idx_pix (int): Index of the pixel to return.
        array_spectra (np.ndarray): An array of shape (2,n) containing spectrum
            data (m/z and intensity) for each pixel.
        array_pixel_indexes (np.ndarray): An array of shape (m,2) containing the boundary indices of
            each pixel in array_spectra.

    Returns:
        np.ndarray: An array of shape (2,m) containing spectrum data (m/z and intensity) for the
            requested pixel.
    """
    # Get the indices of the spectrum of the requested pixel
    idx_1, idx_2 = array_pixel_indexes[idx_pix]
    if idx_1 == -1:
        idx_2 == -2  # To return empty list in the end
    return array_spectra[:, idx_1 : idx_2 + 1]


@njit
def add_zeros_to_spectrum(array_spectra, pad_individual_peaks=True, padding=10**-5):
    """This function adds zeros in-between the peaks of the spectra contained in array_spectra (e.g.
    to be able to plot them as scatterplotgl).

    Args:
        array_spectra (np.ndarray): An array of shape (2,n) containing spectrum data (m/z and
            intensity) for each pixel.
        pad_individual_peaks (bool, optional): If true, pads the peaks individually, with a given
            threshold distance between two m/z values to consider them as belonging to the same
            peak. Else, it pads all single value in the spectrum with zeros. Defaults to False.
        padding (float, optional): The m/z distance between a peak value and a zero for the padding.
            Default to 10**-5.

    Returns:
        (np.ndarray, np.ndarray): An array of shape (2,m) containing the padded spectrum data (m/z
            and intensity) and an array of shape (k,) containing the number of zeros added at each
            index of array_spectra.

    """
    # For speed, allocate array of maximum size
    new_array_spectra = np.zeros(
        (array_spectra.shape[0], array_spectra.shape[1] * 3), dtype=np.float32
    )
    array_index_padding = np.zeros((array_spectra.shape[1]), dtype=np.int32)

    # Either pad each peak individually
    if pad_individual_peaks:
        pad = 0

        # Loop over m/z values
        for i in range(array_spectra.shape[1] - 1):

            # If there's a discontinuity between two peaks, pad with zeros
            if array_spectra[0, i + 1] - array_spectra[0, i] >= 2 * 10**-4:

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

                # Record that 2 zeros have been added between idx i and i+1
                array_index_padding[i] = 2

                # Right peak added in the next loop iteration

            # Else, just store the values of array_spectra without padding
            else:
                # logging.info("two near peaks")
                new_array_spectra[0, i + pad] = array_spectra[0, i]
                new_array_spectra[1, i + pad] = array_spectra[1, i]

        # Add the last value of array_spectra
        new_array_spectra[0, array_spectra.shape[1] + pad - 1] = array_spectra[0, -1]
        new_array_spectra[1, array_spectra.shape[1] + pad - 1] = array_spectra[1, -1]
        return new_array_spectra[:, : array_spectra.shape[1] + pad], array_index_padding

    # Or pad each m/z value individually
    else:

        # Loop over m/z values
        for i in range(array_spectra.shape[1]):
            # Store old array in a regular grid in the extended array
            new_array_spectra[0, 3 * i + 1] = array_spectra[0, i]
            new_array_spectra[1, 3 * i + 1] = array_spectra[1, i]

            # Add zeros in the remaining slots
            new_array_spectra[0, 3 * i] = array_spectra[0, i] - padding
            new_array_spectra[0, 3 * i + 2] = array_spectra[0, i] + padding

            # Record that 2 zeros have been added between idx i and i+1
            array_index_padding[i] = 2

        return new_array_spectra, array_index_padding


@njit
def compute_zeros_extended_spectrum_per_pixel(idx_pix, array_spectra, array_pixel_indexes):
    """This function computes a zero-extended version of the spectrum of pixel indexed by idx_pix.

    Args:
        idx_pix (int): Index of the pixel to return.
        array_spectra (np.ndarray): An array of shape (2,n) containing spectrum
            data (m/z and intensity) for each pixel.
        array_pixel_indexes (np.ndarray): An array of shape (m,2) containing the boundary indices of
            each pixel in array_spectra.

    Returns:
        np.ndarray: An array of shape (2,m) containing the zero-padded spectrum data (m/z and
            intensity) for the requested pixel.
    """
    array_spectra = return_spectrum_per_pixel(idx_pix, array_spectra, array_pixel_indexes)
    new_array_spectra, array_index_padding = add_zeros_to_spectrum(array_spectra)
    return new_array_spectra


@njit
def reduce_resolution_sorted_array_spectra(array_spectra, resolution=10**-3):
    """Recompute a sparce representation of the spectrum at a lower (fixed) resolution, summing over
        the redundant bins. Resolution should be <=10**-4 as it's about the maximum precision
        allowed by float32.

    Args:
        array_spectra (np.ndarray): An array of shape (2,n) containing spectrum
            data (m/z and intensity) for each pixel.
        resolution (float, optional): The size of the bin used to merge intensities. Defaults
            to 10**-3.

    Returns:
        (np.ndarray): Array of shape=(2, m) similar to the input array but with a new sampling
            resolution.
    """
    # Get the re-sampled m/z and intensities from mspec library, with max_intensity = False to sum
    # over redundant bins
    new_mz, new_intensity = reduce_resolution_sorted(
        array_spectra[0, :], array_spectra[1, :], resolution, max_intensity=False
    )

    # Build a new array as the stack of the two others
    new_array_spectra = np.empty((2, new_mz.shape[0]), dtype=np.float32)
    new_array_spectra[0, :] = new_mz
    new_array_spectra[1, :] = new_intensity
    return new_array_spectra


# ! Very similar function in maldi_data... need to harmonize that


@njit
def compute_standardization(array_spectra_pixel, idx_pixel, array_peaks, array_corrective_factors):
    """This function takes the spectrum data of a given pixel, along with the corresponding pixel
    index, and transforms the value of the lipids intensities annotated in 'array_peaks' according
    to the transformation registered in 'array_corrective_factors'.

    Args:
        array_spectra (np.ndarray): A numpy array containing spectrum data (m/z and intensity) of
            pixel 'idx_pixel', sorted by mz.
        idx_pixel (int): Index of the current pixel whose spectrum is transformed.
        array_peaks (np.ndarray): A numpy array containing the peak annotations (min peak, max peak,
            average value of the peak), filtered for the lipids who have preliminarily been
            transformed. Sorted by min_mz.
        array_corrective_factors (np.ndarray): A numpy array of shape (n_lipids, image_shape[0],
            image_shape[1]) containing the corrective factors for the lipids we want to visualize,
            for each pixel.

    Returns:
        np.ndarray: A numpy array containing spectrum data (pixel index, m/z and intensity), of
            pixel 'idx_pixel', sorted by mz, with lipids values transformed.
    """
    # Define initial values
    idx_peak = 0
    idx_mz = 0
    n_peaks_transformed = 0
    while idx_mz < array_spectra_pixel.shape[0] and idx_peak < array_peaks.shape[0]:
        mz, intensity = array_spectra_pixel[idx_mz]
        min_mz, max_mz, mz_estimated = array_peaks[idx_peak]

        # new window has been discovered
        if mz >= min_mz and mz <= max_mz:
            idx_min_mz = idx_mz
            idx_max_mz = idx_mz
            for idx_mz in range(idx_min_mz, array_spectra_pixel.shape[0]):
                mz, intensity = array_spectra_pixel[idx_mz]
                if mz > max_mz:
                    idx_max_mz = idx_mz - 1
                    break

            # Most likely, the annotation doesn't exist, so skip it
            if np.abs(idx_max_mz - idx_min_mz) <= 0.9:
                # zero-out value that do not belong to the MAIA-transformed regions
                array_spectra_pixel[idx_mz, 1] = 0
            # Else compute a multiplicative factor
            else:

                # Get array of intensity before and after correction for current pixel
                correction = array_corrective_factors[idx_peak].flatten()[idx_pixel]

                # Multiply all intensities in the window by the corrective coefficient
                array_spectra_pixel[idx_min_mz : idx_max_mz + 1, 1] *= correction
                n_peaks_transformed += 1

            # Move on to the next peak
            idx_peak += 1

        else:
            if mz > max_mz:
                idx_peak += 1
            else:
                # zero-out value that do not belong to the MAIA-transformed regions
                array_spectra_pixel[idx_mz, 1] = 0
                idx_mz += 1

    return array_spectra_pixel, n_peaks_transformed


@njit
def compute_spectrum_per_row_selection(
    list_index_bound_rows,
    list_index_bound_column_per_row,
    array_spectra,
    array_pixel_indexes,
    image_shape,
    array_peaks_transformed_lipids,
    array_corrective_factors,
    zeros_extend=True,
    apply_correction=False,
):
    """This function computes the average spectrum from a manual selection of rows of pixel (each
    containing a spectrum). The resulting average array can be zero-padded.

    Args:
        list_index_bound_rows (list(tuple)): A list of lower and upper indices delimiting the range
            of rows belonging to the current selection.
        list_index_bound_column_per_row (list(list)): For each row (outer list), provides the index
            of the columns delimiting the current selection (inner list).
        array_spectra (np.ndarray): An array of shape (2,n) containing spectrum
            data (m/z and intensity) for each pixel.
        array_pixel_indexes (np.ndarray): An array of shape (m,2) containing the boundary indices of
            each pixel in array_spectra.
        image_shape (int, int): A tuple of integers, indicating the vertical and horizontal sizes of
            the current slice.
        array_peaks_transformed_lipids (np.ndarray): A numpy array containing the peak annotations
            (min peak, max peak, number of pixels containing the peak, average value of the peak),
            filtered for the lipids who have preliminarily been transformed. Sorted by min_mz.
        array_corrective_factors (np.ndarray): A numpy array of shape (n_lipids, image_shape[0],
            image_shape[1]) containing the corrective factors for the lipids we want to visualize,
            for each pixel.
        zeros_extend (bool, optional): If True, the resulting spectrum will be zero-padded. Defaults
            to True.
        apply_correction (bool, optional): If True, MAIA transformation is applied to the lipids
            belonging to array_peaks_transformed_lipids, for each pixel. This option makes the
            computation very slow, so it shouldn't be selected if the computations must be done on
            the fly. Defaults to False.

    Returns:
        np.ndarray: Spectrum averaged from a manual selection of rows of pixel, containing m/z
            values in the first row, and intensities in the second row.
    """
    # Get list of row indexes for the current selection
    ll_idx, size_array, ll_idx_pix = get_list_row_indexes(
        list_index_bound_rows, list_index_bound_column_per_row, array_pixel_indexes, image_shape
    )

    # Init array selection of size size_array
    array_spectra_selection = np.zeros((2, size_array), dtype=np.float32)
    pad = 0

    # Fill array line by line
    for i, x in enumerate(range(list_index_bound_rows[0], list_index_bound_rows[1] + 1)):
        for idx_1, idx_2, idx_pix_1, idx_pix_2 in zip(
            ll_idx[i][0:-1:2], ll_idx[i][1::2], ll_idx_pix[i][0:-1:2], ll_idx_pix[i][1::2]
        ):
            if apply_correction:
                for idx_pix in range(idx_pix_1, idx_pix_2 + 1):
                    idx_mz_1, idx_mz_2 = array_pixel_indexes[idx_pix]
                    # If the pixel is not empty
                    if idx_mz_2 - idx_mz_1 > 0:
                        array_spectra_pix_to_correct = array_spectra[
                            :, idx_mz_1 : idx_mz_2 + 1
                        ].copy()
                        array_spectra_pix_corrected, n_peaks_transformed = compute_standardization(
                            array_spectra_pix_to_correct.T,
                            idx_pix,
                            array_peaks_transformed_lipids,
                            array_corrective_factors,
                        )
                        array_spectra_selection[
                            :, pad : pad + idx_mz_2 + 1 - idx_mz_1
                        ] = array_spectra_pix_corrected.T
                        pad += idx_mz_2 + 1 - idx_mz_1
            else:
                array_spectra_selection[:, pad : pad + idx_2 + 1 - idx_1] = array_spectra[
                    :, idx_1 : idx_2 + 1
                ]
                pad += idx_2 + 1 - idx_1

    # Sort array
    array_spectra_selection = array_spectra_selection[:, array_spectra_selection[0].argsort()]

    # Remove the values that have been zeroed-out
    if apply_correction:
        array_spectra_selection = strip_zeros(array_spectra_selection)

    # Sum the arrays (similar m/z values are added)
    array_spectra_selection = reduce_resolution_sorted_array_spectra(
        array_spectra_selection, resolution=10**-4
    )

    # Pad with zeros if asked
    if zeros_extend:
        array_spectra_selection, array_index_padding = add_zeros_to_spectrum(
            array_spectra_selection
        )
    return array_spectra_selection


@njit
def get_list_row_indexes(
    list_index_bound_rows, list_index_bound_column_per_row, array_pixel_indexes, image_shape
):
    """This function turns a selection of rows (bounds in list_index_bound_rows) and corresponding
    columns (bounds in list_index_bound_column_per_row) into an optimized list of pixel indices in
    array_spectra. It takes advantage of the fact that pixels that are neighbours in a given rows
    also have contiguous spectra in array_spectra, allowing for faster query.

    Args:
        list_index_bound_rows (list(tuple)): A list of lower and upper indices delimiting the range
            of rows belonging to the current selection.
        list_index_bound_column_per_row (list(list)): For each row (outer list), provides the index
            of the columns delimiting the current selection (inner list).
        array_pixel_indexes (np.ndarray): An array of shape (m,2) containing the boundary indices of
            each pixel in array_spectra.
        image_shape (int, int): A tuple of integers, indicating the vertical and horizontal sizes of
            the current slice.

    Returns:
        (list(list): List of 2-elements lists which contains the mz indices (inner list) in
            array_spectra of the extrema pixel for each row (outer list).
        int: Total size of the concatenated spectra indexed
        list(list)):  List of 2-elements lists which contains pixels indices (inner list) in
            array_spectra of the extrema pixel for each row (outer list).
    """
    # Compute size array
    size_array = 0
    ll_idx = []
    ll_idx_pix = []
    # Loop over rows in the selection
    for i, x in enumerate(range(list_index_bound_rows[0], list_index_bound_rows[1] + 1)):
        # Careful: list_index_bound_column_per_row
        l_idx = []
        l_idx_pix = []
        for j in range(0, len(list_index_bound_column_per_row[i]), 2):
            # Check if we're not just looping over zero padding
            if (
                list_index_bound_column_per_row[i][j] == 0
                and list_index_bound_column_per_row[i][j + 1] == 0
            ):
                continue

            # Get the outer indexes of the (concatenated) spectra of the current row belonging to
            # the selection
            idx_pix_1 = convert_coor_to_spectrum_idx(
                (x, list_index_bound_column_per_row[i][j]), image_shape
            )
            idx_1 = array_pixel_indexes[idx_pix_1, 0]
            idx_pix_2 = convert_coor_to_spectrum_idx(
                (x, list_index_bound_column_per_row[i][j + 1]), image_shape
            )
            idx_2 = array_pixel_indexes[idx_pix_2, 1]

            # Case we started or finished with empty pixel
            if idx_1 == -1 or idx_2 == -1:

                # Move forward until a non-empty pixel is found for idx_1
                j = 1
                while idx_1 == -1:
                    idx_1 = array_pixel_indexes[idx_pix_1 + j, 0]
                    j += 1
                idx_pix_1 = idx_pix_1 + j - 1

                # Move backward until a non-empty pixel is found for idx_2
                j = 1
                while idx_2 == -1:
                    idx_2 = array_pixel_indexes[idx_pix_2 - j, 1]
                    j += 1
                idx_pix_2 = idx_pix_2 + j - 1

            # Check that we still have idx_2>=idx_1
            if idx_1 > idx_2:
                pass
            else:
                size_array += idx_2 + 1 - idx_1
                l_idx.extend([idx_1, idx_2])
                l_idx_pix.extend([idx_pix_1, idx_pix_2])

        # Add the couple of spectra indexes to the list
        ll_idx.append(l_idx)
        ll_idx_pix.append(l_idx_pix)
    return ll_idx, size_array, ll_idx_pix


@njit
def sample_rows_from_path(path):
    """This function takes a path as input and returns the lower and upper indexes of the rows
    belonging to the current selection (i.e. indexed in the path), as well as the corresponding
    column boundaries for each row. Note that, although counter-intuitive given the kind of
    regression done in this function, x is the vertical axis (from top to bottom), and y the
    horizontal one.

    Args:
        path (np.ndarray): A two-dimensional array, containing, in each row, the row and column
        coordinates (x and y) of the current selection.

    Returns:
        (np.ndarray, np.ndarray): The first array contains the lower and upper indexes of the rows
        belonging to the current selection. The second array contains, for each row, the
        corresponding column boundaries (there can be more than 2 for non-convex shapes).
    """
    # Find out the lower and upper rows
    x_min = path[:, 0].min()
    x_max = path[:, 0].max()

    # Numba won't accept a list of list, so I must use a list of np arrays for the column boundaries
    list_index_bound_column_per_row = [np.arange(0) for x in range(x_min, x_max + 1)]

    # Also register the x-axis direction to correct the linear regression accordingly
    dir_prev = None

    # For each couple of points in the path, do a linear regression to find the corresponding y
    # (needed due to non constant sampling on the y-axis)
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

    # Min x and max x often cover only zero or one pixel due to the way the sampling is done, we
    # just get rid of them
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
            # logging.warning("Bug with list x", x, list_index_bound_column_per_row[x - x_min])
            # Try to correct the number of times x appear
            if (
                len(list_index_bound_column_per_row[x - x_min]) % 2 == 1
                and len(list_index_bound_column_per_row[x - x_min]) != 1
            ):
                list_index_bound_column_per_row[x - x_min] = list_index_bound_column_per_row[
                    x - x_min
                ][:-1]
            else:
                list_index_bound_column_per_row[x - x_min] = np.append(
                    list_index_bound_column_per_row[x - x_min],
                    list_index_bound_column_per_row[x - x_min][0],
                )
        list_index_bound_column_per_row[x - x_min].sort()  # Inplace sort to spare memory

    # Convert list of np.array to np array padded with zeros (for numba compatibility)
    max_len = max([len(i) for i in list_index_bound_column_per_row])
    array_index_bound_column_per_row = np.zeros(
        (len(list_index_bound_column_per_row), max_len), dtype=np.int32
    )
    for i, arr in enumerate(list_index_bound_column_per_row):
        array_index_bound_column_per_row[i, : len(arr)] = arr

    return np.array([x_min, x_max], dtype=np.int32), array_index_bound_column_per_row


@njit
def return_index_labels(l_min, l_max, l_mz, zero_padding_extra=5 * 10**-5):
    """This function returns the corresponding lipid name indices from a list of m/z values. Note
    that the zero_padding_extra parameter is needed for both taking into account the zero-padding
    (this way zeros on the sides of the peak are also identified as the annotated lipid) but also
    because the annotation is very stringent in the first place, and sometimes border of the peaks
    are missing in the annotation.

    Args:
        l_min (list(int)): This list provides the lower peak boundaries of the identified lipids.
        l_max (list(int)): This list provides the upper peak boundaries of the identified lipids.
        l_mz (list(float)): The list of m/z value which must be annotated with lipid names.
        zero_padding_extra (float, optional): Size of the zero-padding. Defaults to 5*10**-5.

    Returns:
        np.ndarray: A 1-dimensional array containing the indices of the lipid labels.
    """
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


@njit
def return_idx_sup(l_idx_labels):
    """Returns the indices of the lipids that have an annotation

    Args:
        l_idx_labels (np.ndarray): A 1-dimensional array containing the indices of the lipid labels.

    Returns:
        np.ndarray: A list containing the indices of the lipids that have an annotation.
    """
    return [i for i, x in enumerate(l_idx_labels) if x >= 0]


@njit
def return_idx_inf(l_idx_labels):
    """Returns the indices of the lipids that do not have an annotation

    Args:
        l_idx_labels (np.ndarray): A 1-dimensional array containing the indices of the lipid labels.

    Returns:
        np.ndarray: A list containing the indices of the lipids that do not have an annotation.
    """
    return [i for i, x in enumerate(l_idx_labels) if x < 0]


@njit
def compute_avg_intensity_per_lipid(l_intensity_with_lipids, l_idx_labels):
    """This function computes the average intensity of each annotated lipid (summing over peaks
    coming from the same lipid) from a given spectrum.

    Args:
        l_intensity_with_lipids (list(float)): A list of peak intensities (where one lipid can
        correspond to several
            peaks, but one peak always correspond to one lipid).
        l_idx_labels (list(int)): A list of lipid annotation, each lipid being annotated with a
        unique integer.

    Returns:
        list(int), list(float): The first list provides the lipid indices, while the second provide
        the lipid average intensities. Peaks corresponding to identical lipid have been averaged.
    """
    # Define empty lists for the lipid indices and intensities
    l_unique_idx_labels = []
    l_avg_intensity = []
    idx_label_temp = -1

    # Loop over the lipid indices (i.e. m/z values)
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


# Not cached as the caching/retrieving takes as long as the function itself
# @cache.memoize()
def global_lipid_index_store(data, slice_index, l_spectra):
    """This function is used to extract the lipid label indexes for a given list of spectra, coming
    from a given slice (slice_index).

    Args:
        data (MaldiData): The object used to access the MALDI data.
        slice_index (int): Index of the current slice.
        l_spectra (list(np.ndarray)): A list of spectra (two dimensional numpy arrays), coming from
            the slice having index slice_index.

    Returns:
        list(list(str)): A list of list of lipid labels, one list per spectrum.
    """
    logging.info("Starting computing ll_idx_labels")
    ll_idx_labels = []
    for spectrum in l_spectra:

        if spectrum is not None:
            # Get the average spectrum and add it to m/z plot
            grah_scattergl_data = np.array(spectrum, dtype=np.float32)

            # Get df for current slice
            df_names = data.get_annotations()[data.get_annotations()["slice"] == slice_index]

            # Extract lipid names
            l_idx_labels = return_index_labels(
                df_names["min"].to_numpy(),
                df_names["max"].to_numpy(),
                grah_scattergl_data[0, :],
            )
        else:
            l_idx_labels = None

        # Save in a list of lists
        ll_idx_labels.append(l_idx_labels)
    logging.info("Returning ll_idx_labels")
    return ll_idx_labels


# ==================================================================================================
# --- Functions for safe multiprocessing and multithreading
# ==================================================================================================


def compute_thread_safe_function(
    compute_function, cache, data, slice_index, *args_compute_function, **kwargs_compute_function
):
    """This function is a wrapper for safe multithreading and multiprocessing execution of
    compute_function. This is needed due to the regular cleansing of memory-mapped object.

    Args:
        compute_function (func): The function/method whose result must be loaded/saved.
        cache (flask_caching.Cache): A caching object, used to check if the reading of memory-mapped
            data is safe
        *args_compute_function: Arguments of compute_function.
        *kwargs_compute_function: Named arguments of compute_function.

    Returns:
        The result of compute_function. Type may vary depending on compute_function.
    """

    logging.info(
        "Trying to compute the thread-safe version of "
        + str(compute_function).split("<")[1].split("at")[0]
    )

    if cache is not None:

        # Wait for the data to be safe for reading
        while cache.get("locked-cleaning"):
            time.sleep(0.05)

        # Lock it while while it's being read
        cache.set("locked-reading", True)

    else:
        logging.warning("No cache provided, the thread unsafe version of the function will be run")

    # Run the actual function
    result = compute_function(*args_compute_function, **kwargs_compute_function)

    if cache is not None:
        # Unlock the data
        cache.set("locked-reading", False)

    if data is not None:
        # Clean the memory-mapped data
        data.clean_memory(slice_index=slice_index, cache=cache)

    # Return result
    return result
