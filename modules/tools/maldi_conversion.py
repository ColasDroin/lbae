# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This file contains functions used to convert the raw MALDI data to easily readable Numpy arrays.
"""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import numpy as np
from numba import njit
import os
import pandas as pd

# LBAE imports
from modules.tools.external_lib.mspec import SmzMLobj
from modules.tools.spectra import reduce_resolution_sorted_array_spectra

# Define if the app uses the whole dataset or not
SAMPLE_APP = False
N_SAMPLES = 3
# ==================================================================================================
# --- Functions
# ==================================================================================================


def load_file(path, resolution=1e-5):
    """This function loads the specified MALDI file from the raw data format (.mzML and .UDP)
    with the given resolution, and turns it into a scipy sparse matrix.

    Args:
        path (string): The path of the file to load.
        resolution (float, optional): The resolution of the file to load. Defaults to 1e-5.

    Returns:
        scipy.sparse: A sparse matrix containing the intensity for each m/z value.
    """
    # Check if imzML exists and load if possible
    if os.path.exists(path + ".imzML"):
        smz = SmzMLobj(path + ".ibd", path + ".imzML", mz_resolution=resolution)
        smz.load(load_unique_mz=True)
    else:
        # Load object from SmzMLobj
        smz = SmzMLobj(path + ".mzML", path + ".UDP", mz_resolution=resolution)
        smz.load(load_unique_mz=True)

    # Compute shape of the spectra matrix to preload matrix
    smz.S.shape
    return smz


def process_sparse_matrix(smz, sort=["Pixel", "m/z"], sample=False):
    """This function converts the space matrix into a dataframe sorted according to the 'sort'
    parameter. It is possible to work only on a tiny subset of the matrix with the 'sample'
    parameter for debugging purposes.

    Args:
        smz (scipy.sparse): The sparse matrix obtained from the MALDI imaging.
        sort (list, optional): A list of column names according to which the final dataframe should
            be sorted. Defaults to ["Pixel", "m/z"].
        sample (bool, optional): A boolean parameter to sample only a subset of the matrix. Defaults
            to False.

    Returns:
        pandas.Dataframe: A sorted dataframe with three columns: pixels index, m/z, and intensity
            value.
    """
    # We're going to slice the matrix row by row, so it's faster to convert to csr rather than csc
    S_row = smz.S.tocsr()

    # Turn S into a dict for later conversion into a dataframe
    dic_spectra = {"Pixel": [], "m/z": [], "Intensity": []}
    for i in range(S_row.shape[0]):
        non_zero_indices = S_row[i, :].nonzero()[1]
        dic_spectra["Pixel"].extend([i] * len(non_zero_indices))
        dic_spectra["m/z"].extend(smz.mz_vals[non_zero_indices])
        dic_spectra["Intensity"].extend(S_row[i, non_zero_indices].toarray().flatten())

        if sample and i == 10:
            break

    # Turn dict into a df for easier manipulation
    df = pd.DataFrame.from_dict(dic_spectra)

    # Sort
    df = df.sort_values(by=sort, axis=0)

    # Store image size as metadata
    df.attrs["image_shape"] = smz.img_shape
    return df


@njit
def compute_TIC_per_pixel(array_spectra, n_pixels):
    """This function computes the Total Ion Content (TIC) per pixel of the raw data.

    Args:
        array_spectra (np.ndarray): A numpy array containing spectrum data (pixel index, m/z and
            intensity).
        n_pixels (int): Number of pixels in the acquisition.

    Returns:
        np.ndarray: A numpy array of len n_pixels containing the TIC for each pixel.
    """
    array_TIC = np.zeros((n_pixels,), dtype=np.float32)
    for i in range(array_spectra.shape[0]):
        pix_idx, mz, intensity = array_spectra[i]
        array_TIC[int(pix_idx)] += intensity
    return array_TIC


@njit
def normalize_per_TIC_per_pixel(array_spectra, array_TIC):
    """This function normalize each intensity value according to its (TIC), per pixel.

    Args:
        array_spectra (np.ndarray): A numpy array containing spectrum data (pixel index, m/z and
            intensity).
        array_TIC (np.ndarray): A numpy array of len n_pixels containing the TIC for each pixel.

    Returns:
        np.ndarray: A numpy array containing TIC-normalized spectrum data (pixel index, m/z and
            intensity).
    """
    for i in range(array_spectra.shape[0]):
        pix_idx, mz, intensity = array_spectra[i]
        array_spectra[i, 2] /= array_TIC[int(pix_idx)]
    return array_spectra


def load_peak_file(path, array=True):
    """This function loads the peaks annotations (including matrix peaks) from a csv file located
    at the provided path. It returns a numpy array sorted by min peak value (m/z) annotation.

    Args:
        path (string): The path of the csv file containing the peaks annotations.

    Returns:
        np.ndarray: The sorted dataframe containing the annotations (min peak, max peak, number of
            pixels containing the current molecule, estimated mz of the current molecule).
    """
    # Load the peaks annotations using the last definition used for the csv file
    path = "/".join(path.split("/")[:-1]) + "/ranges"
    df = pd.read_csv(path + ".csv", sep=",")

    # Drop the columns that we won't use afterwards
    df = df.drop(
        [
            "Unnamed: 0",
            "pixel_max_hits",
            "percent_1_hit",
            "concentration",
            "median_intensity",
            "difference",
        ],
        axis=1,
    )

    # Sort by increasing m/z annotation for the peaks
    df = df.sort_values(by="min", axis=0)
    if array:
        return df.to_numpy()
    else:
        return df


def load_lipid_file(section_index, path):
    """This function loads a set of specific lipid annotations containing a molecule ID, the average
    mz for the molecule, the section index and potentially other information, from a csv file
    located at the provided path. It returns an array of mz values corresponding to the lipids we
    want to keep for further visualization.

    Args:
        section_index (int): The index of the current acquisition (first slice having index 1).
        path (string): The path of the csv file containing the lipids annotations.

    Returns:
        np.ndarray: A two-dimensional array of m/z values corrsponding to the lipids that we want to
            keep for further visualization (first column is per-slice value, second column is
            averaged value). Sorted by individual slice value in the end.
    """
    # Load the peaks annotations using the last definition used for the csv file
    df = pd.read_csv(path, sep=",")

    # Drop the columns that we won't use afterwards
    df = df.drop(
        [
            "molecule_ID",
            "concentration",
        ],
        axis=1,
    )

    # Keep only the current section
    df = df[df["section_ix"] == section_index - 1]

    # Return a numpy array of mz values sorted by first column
    array_mz_lipids = np.array(df[["mz_estimated", "mz_estimated_total"]], dtype=np.float32)
    return array_mz_lipids[np.argsort(array_mz_lipids[:, 0])]


@njit
def filter_peaks(array_spectra, array_peaks, array_mz_lipids_per_slice):
    """This function is used to filter out all the spectrum data in 'array_spectra' that
    has not been annotated as peak in 'array_peaks' and that do not belong to
    'array_mz_lipids_per_slice'.

    Args:
        array_spectra (np.ndarray): A numpy array containing spectrum data (pixel index, m/z and
            intensity), sorted by mz (but not necessarily by pixel index).
        array_peaks (np.ndarray): A numpy array containing the peak annotations (min peak, max peak,
            number of pixels containing the peak, average value of the peak), sorted by min_mz.
        array_mz_lipids_per_slice (np.ndarray): A 1-D numpy array containing the per-slice mz
            values of the lipids we want to visualize.

    Returns:
        list: m/z values corresponding to peaks that have been annotated and belong to lipids we
            want to visualize.
        list: m/z values of the lipids the lipids we want to visualize that have been kept.
    """
    # Define initial values
    l_to_keep = []
    idx_peak = 0
    idx_curr_mz = 0
    idx_lipid = 0
    l_n_pix = []
    mz_lipid = array_mz_lipids_per_slice[idx_lipid]
    l_mz_lipids_kept = []
    # Need to initialize the set with an int inside and then delete it because numba is retarded
    set_pix = {0}
    set_pix.remove(0)

    while idx_curr_mz < array_spectra.shape[0] and idx_peak < array_peaks.shape[0]:
        idx_pix, mz, intensity = array_spectra[idx_curr_mz]
        min_mz, max_mz, n_pix, mz_estimated = array_peaks[idx_peak]

        # Either we are before the current window
        if mz <= min_mz:
            idx_curr_mz += 1

        # Either current mz is in the current window
        elif mz >= min_mz and mz <= max_mz:
            # Adapt the index of the current lipid
            while mz_lipid < min_mz and idx_lipid < array_mz_lipids_per_slice.shape[0]:
                idx_lipid += 1
                mz_lipid = array_mz_lipids_per_slice[idx_lipid]

            # If we've explored all lipids already, exit the loop
            if idx_lipid == array_mz_lipids_per_slice.shape[0]:
                break

            # If mz lipid is not in the current peak, move on to the next
            if mz_lipid > max_mz or np.abs(mz_estimated - mz_lipid) > 2 * 10**-4:
                idx_peak += 1
                l_n_pix.append(len(set_pix))
                set_pix.clear()
            else:
                # mz belong to a lipid we want to visualize
                l_to_keep.append(idx_curr_mz)
                set_pix.add(idx_pix)
                idx_curr_mz += 1
                if len(l_mz_lipids_kept) == 0:
                    l_mz_lipids_kept.append(mz_lipid)
                elif mz_lipid != l_mz_lipids_kept[-1]:
                    l_mz_lipids_kept.append(mz_lipid)

        # Either we're beyond, in which cas we move the window, and record the number of unique
        # pixels in the window for later check
        else:
            idx_peak += 1
            l_n_pix.append(len(set_pix))
            set_pix.clear()

    # * This piece of code is commented because it is not usable as such since the introduction of
    # * array_mz_lipids_per_slice as argument in the function, but it should still work if molecules
    # * not belonging to array_mz_lipids_per_slice are not excluded
    # if verbose:
    #     # Check that the pixel recorded are identical to the expected number of pixels recorded
    #     print(
    #         "Difference between number of recorded pixels",
    #         np.sum(np.array(l_n_pix) - array_peaks[:, 2]),
    #     )
    #     print(np.array(l_n_pix)[-10:])
    #     print(array_peaks[-10:, 2])

    return l_to_keep, l_mz_lipids_kept


@njit
def return_array_pixel_indexes(array_pixel, total_shape):
    """This function returns an array of pixel indexes: for each pixel (corresponding to the index
    of a given row of array_pixel_indexes), it returns the 2 boundaries in the corresponding
    array_spectra (upper boundarie is included).

    Args:
        array_pixel (np.ndarray): Array of length n containing the index of each pixel for each m/z
            value.
        total_shape (int): Total number of pixels in the slice.

    Returns:
        np.ndarray: An array of shape (m,2) containing the boundary indices of each pixel in the
            original spectra array.
    """
    array_pixel_indexes = np.empty((total_shape, 2), dtype=np.int32)
    array_pixel_indexes.fill(-1)
    for i, p in enumerate(array_pixel):
        # First time pixel is encountered
        if array_pixel_indexes[p, 0] == -1:
            array_pixel_indexes[p, 0] = i
        # Last time pixel is encountered
        array_pixel_indexes[p, 1] = i
    return array_pixel_indexes


def get_standardized_values(
    slice_index,
    path_array_data,
    path_array_transformed_data,
):
    """This function loads the values of the intensities of the the lipids whose expression have
    been previously corrected using MAIA.

    Args:
        slice_index (int): Index of the current acquisition.
        path_array_data (str, optional): Path of the lipid intensities before transformation.
            Defaults to "/data/lipidatlas/data/processed/BRAIN1".
        path_array_transformed_data (str, optional): Path of the lipid intensities after
            transformation. Defaults to "/data/lipidatlas/data/processed/BRAIN1_normalized".

    Raises:
        ValueError: Some lipids have been transformed but the initial (untransformed) expression
            data is missing.

    Returns:
        list, list, np.array, np.array : 2 lists and 2 arrays containing respectively:
            - The name of the folders containing the transformed lipid expression. The name is a
                string representing the mz value itself.
            - The corresponding mz values as floats.
            - The array of expression before transformation (having the same shape as the original
                acquisition).
            - The array of expression after transformation (having the same shape as the original
                acquisition).
    """
    # First get list of lipids for which a transformation has been applied
    l_lipids_str = os.listdir(path_array_data)
    l_lipids_str_transformed = os.listdir(path_array_transformed_data)

    # Return empty lists if no MALDI files exist yet
    if len(l_lipids_str) == 0 and len(l_lipids_str_transformed) == 0:
        return [], [], np.array([], dtype=np.float32), np.array([], dtype=np.float32)

    # Keep only lipid that have been transformed
    l_lipids_str = [x for x in l_lipids_str if x in l_lipids_str_transformed]

    # Assess that the two lists are identical
    if l_lipids_str != l_lipids_str_transformed:
        raise ValueError("The lipids before and after transformation are not the same")

    # Convert filename to float mz value
    l_lipids_float = [float(x) for x in l_lipids_str]
    # Sort the two lists by increasing m/z
    l_lipids_str, l_lipids_float = zip(*sorted(zip(l_lipids_str, l_lipids_float)))

    # Get the corresponding numpy arrays
    l_arrays_before_transfo = []
    l_arrays_after_transfo = []
    l_to_keep = []
    for idx, lipid_str in enumerate(l_lipids_str):

        try:
            array_before_transfo = np.load(
                path_array_data + "/" + lipid_str + "/" + str(slice_index - 1) + ".npy"
            )

        except:
            # If the array doesn't exist, it means that the lipid doesn't exist for the current slice
            continue

        array_after_transfo = np.load(
            path_array_transformed_data + "/" + lipid_str + "/" + str(slice_index - 1) + ".npy"
        )

        l_arrays_before_transfo.append(array_before_transfo)
        l_arrays_after_transfo.append(array_after_transfo)
        l_to_keep.append(idx)
    return (
        [x for x in l_lipids_str if x in l_to_keep],
        [x for x in l_lipids_float if x in l_to_keep],
        np.array(l_arrays_before_transfo, dtype=np.float32),
        np.array(l_arrays_after_transfo, dtype=np.float32),
    )


# * Caution, a very similar function is also in spectra.py, meaning that if a change is made here,
# * it should probably be made there too
@njit
def compute_standardization(
    array_spectra_pixel, idx_pixel, array_peaks, arrays_before_transfo, arrays_after_transfo
):
    """This function takes the spectrum data of a given pixel, along with the corresponding pixel
    index, and transforms the value of the lipids intensities annotated in 'array_peaks' according
    to the transformation made in 'arrays_before_transfo' and 'arrays_after_transfo'.

    Args:
        array_spectra (np.ndarray): A numpy array containing spectrum data (pixel index, m/z and
            intensity) of pixel 'idx_pixel', sorted by mz.
        idx_pixel (int): Index of the current pixel whose spectrum is transformed.
        array_peaks (np.ndarray): A numpy array containing the peak annotations (min peak, max peak,
            number of pixels containing the peak, average value of the peak), filtered for the
            lipids who have preliminarily been transformed. Sorted by min_mz.
        arrays_before_transfo (np.ndarray): A numpy array of shape (n_lipids, image_shape[0],
            image_shape[1]) containing the cumulated intensities (summed over all bins) of the
            lipids we want to visualize, for each pixel, before these intensities were transformed.
        arrays_after_transfo (np.ndarray): A numpy array of shape (n_lipids, image_shape[0],
            image_shape[1]) containing the cumulated intensities (summed over all bins) of the
            lipids we want to visualize, for each pixel, after these intensities were transformed.

    Raises:
        Exception: _description_

    Returns:
        np.ndarray: A numpy array containing spectrum data (pixel index, m/z and intensity), of
            pixel 'idx_pixel', sorted by mz, with lipids values transformed.
    """
    # Define initial values
    idx_peak = 0
    idx_mz = 0
    n_peaks_transformed = 0
    while idx_mz < array_spectra_pixel.shape[0] and idx_peak < array_peaks.shape[0]:
        idx_pix, mz, intensity = array_spectra_pixel[idx_mz]
        min_mz, max_mz, n_pix, mz_estimated = array_peaks[idx_peak]

        # New window has been discovered
        if mz >= min_mz and mz <= max_mz:
            idx_min_mz = idx_mz
            idx_max_mz = idx_mz
            for idx_mz in range(idx_min_mz, array_spectra_pixel.shape[0]):
                idx_pix, mz, intensity = array_spectra_pixel[idx_mz]
                if mz > max_mz:
                    idx_max_mz = idx_mz - 1
                    break

            # Most likely, the annotation doesn't exist, so skip it
            if np.abs(idx_max_mz - idx_min_mz) <= 0.9:
                pass

            # Else compute a multiplicative factor
            else:

                # Get array of intensity before and after correction for current pixel
                intensity_before = arrays_before_transfo[idx_peak].flatten()[idx_pixel]
                intensity_after = arrays_after_transfo[idx_peak].flatten()[idx_pixel]

                # Compute sum of expression between limits
                integral = np.sum(array_spectra_pixel[idx_min_mz : idx_max_mz + 1, 2])

                # Assess that this sum is equal to the one precomputed with MAIA
                if np.abs(integral - intensity_before) > 10**-4:
                    print("There seems to be a problem with the computation of the integral")
                    print(integral, intensity_before)
                    print(idx_min_mz, idx_max_mz)

                else:
                    # print(integral, intensity_before)
                    # print(idx_min_mz, idx_max_mz)
                    pass

                # To avoid division by 0 (altough it shouldn't happen)
                if intensity_before == 0:
                    intensity_before = 1

                correction = intensity_after / intensity_before

                # Correct for negative values for very small corrections
                if correction < 0:
                    correction = 0

                # Multiply all intensities in the window by the corrective coefficient
                array_spectra_pixel[idx_min_mz : idx_max_mz + 1, 2] *= correction
                n_peaks_transformed += 1

            # Move on to the next peak
            idx_peak += 1

        else:
            if mz > max_mz:
                idx_peak += 1
            else:
                idx_mz += 1

    return array_spectra_pixel, n_peaks_transformed


def get_array_peaks_to_correct(l_lipids_float, array_mz_lipids, array_peaks, slice_index=None):
    """This function computes an array similar to 'array_peaks', but containing only the lipids that
    have been MAIA-transformed.

    Args:
        l_lipids_float (list): A list containing the estimated m/z values of the lipids we want to
            visualize.
        array_mz_lipids_per_slice (np.ndarray): A 1-D numpy array containing the per-slice mz
            values of the lipids we want to visualize.
        array_peaks (np.ndarray): A numpy array containing the peak annotations (min peak, max peak,
            number of pixels containing the peak, average value of the peak), sorted by min_mz.
    Returns:
        np.ndarray: A numpy array similar to 'array_peaks', but containing only the lipids that have
            been MAIA-transformed.
    """
    # Low precision as the reference can be quite different from the actual m/z value estimated
    precision = 5 * 10**-3

    # First get the list of mz of the current slice
    l_lipids_float_correct = []
    for mz_lipid in l_lipids_float:
        found = False
        # Find the closest value in the whole array of annotations
        idx_closest_value = (np.abs(array_mz_lipids[:, 1] - mz_lipid)).argmin()
        mz_per_slice, mz_avg = array_mz_lipids[idx_closest_value]
        diff = np.abs(mz_avg - mz_lipid)
        if diff <= precision:
            l_lipids_float_correct.append(mz_per_slice)
            found = True
        if not found:
            print("Could not find the annotation of the lipid {} in df_match.csv".format(mz_lipid))
            print("Closest mz value found was {}".format(mz_avg))
            if slice_index is not None:
                print("Slice index was {}".format(slice_index - 1))
            raise Exception

        # for mz_per_slice, mz_avg in array_mz_lipids:
        #     if np.abs(mz_avg - mz_lipid) <= precision:
        #         found = True
        #         l_lipids_float_correct.append(mz_per_slice)
        #         break
        # if not found:
        #     raise Exception("No lipid could be found for foldername with mz = " + str(mz_lipid))

    # keep only the peak annotation that correspond to the lipids which have been transformed
    rows_to_keep = []
    # Take higher precision as values should be perfectly identical here
    precision = 10**-4
    for mz_lipid in l_lipids_float_correct:
        found = False
        for idx, [mini, maxi, npix, mz_est] in enumerate(array_peaks):
            if np.abs(mz_est - mz_lipid) <= precision:
                found = True
                rows_to_keep.append(idx)
                break
        if not found:
            print(
                "Lipid with foldername with mz = "
                + str(mz_lipid)
                + " was in df_match.csv but not in ranges.csv"
            )
            if slice_index is not None:
                print("Slice index was {}".format(slice_index - 1))
            raise Exception
    array_peaks_to_correct = array_peaks[rows_to_keep]

    return array_peaks_to_correct


def standardize_values(
    array_spectra,
    array_pixel_indexes,
    array_peaks,
    array_mz_lipids,
    l_lipids_float,
    arrays_before_transfo,
    arrays_after_transfo,
    array_peaks_to_correct,
    ignore_standardization=True,
):
    """This function rescale the intensity values of the lipids annotated with a Combat-like method
    as part of the MAIA pipeline, using pre-computed intensities values.

    Args:
        array_spectra (np.ndarray): A numpy array containing spectrum data (pixel index, m/z and
            intensity), sorted by pixel index and mz.
        array_pixel_indexes (np.ndarray): A numpy array of shape (m,2) containing the boundary
            indices of each pixel in the original spectra array.
        array_peaks (np.ndarray): A numpy array containing the peak annotations (min peak, max peak,
            number of pixels containing the peak, average value of the peak), sorted by min_mz.
        array_mz_lipids_per_slice (np.ndarray): A 1-D numpy array containing the per-slice mz
            values of the lipids we want to visualize.
        l_lipids_float (list): A list containing the estimated m/z values of the lipids we want to
            visualize.
        arrays_before_transfo (np.ndarray): A numpy array of shape (n_lipids, image_shape[0],
            image_shape[1]) containing the cumulated intensities (summed over all bins) of the
            lipids we want to visualize, for each pixel, before these intensities were transformed.
        arrays_after_transfo (np.ndarray): A numpy array of shape (n_lipids, image_shape[0],
            image_shape[1]) containing the cumulated intensities (summed over all bins) of the
            lipids we want to visualize, for each pixel, after these intensities were transformed.
        array_peaks_to_correct (np.ndarray): A numpy array similar to 'array_peaks', but containing
            only the lipids that have been MAIA-transformed.
        ignore_standardization (bool): If True, the standardization step is ignored. The function
            is not useless as it still returns 'array_peaks_to_correct' and
            'array_corrective_factors'.
    Returns:
        np.ndarray: A numpy array containing spectrum data (pixel index, m/z and intensity), sorted
            by pixel index and mz, with lipids values transformed.
        np.ndarray: A numpy array similar to 'array_peaks', but containing only the lipids that have
            been transformed.
        np.ndarray: A numpy array equal to the ratio of 'arrays_after_transfo' and
            'arrays_before_transfo' containing the corrective factor used for lipid and each pixel.
    """

    if not ignore_standardization:
        # Compute the transformed spectrum for each pixel
        n_pix_transformed = 0
        sum_n_peaks_transformed = 0
        for idx_pixel, [idx_pixel_min, idx_pixel_max] in enumerate(array_pixel_indexes):
            array_spectra_pixel = array_spectra[idx_pixel_min : idx_pixel_max + 1]
            if len(array_spectra_pixel) > 1:
                array_spectra_pixel, n_peaks_transformed = compute_standardization(
                    array_spectra_pixel,
                    idx_pixel,
                    array_peaks_to_correct,
                    arrays_before_transfo,
                    arrays_after_transfo,
                )

                # Reattribute the corrected values to the intial spectrum
                array_spectra[idx_pixel_min : idx_pixel_max + 1] = array_spectra_pixel
                n_pix_transformed += 1
                sum_n_peaks_transformed += n_peaks_transformed

        print(
            n_pix_transformed,
            "have been transformed, with an average of ",
            sum_n_peaks_transformed / n_pix_transformed,
            "peaks transformed",
        )
    # Delete the n_pix column (3rd column) in array_peaks
    array_peaks_to_correct = np.delete(array_peaks_to_correct, 2, 1)

    # Get the array of corrective factors (per lipid per pixel), removing zero values
    array_corrective_factors = np.array(
        np.nan_to_num(arrays_after_transfo / arrays_before_transfo), dtype=np.float16
    )

    # Correct for negative values
    array_corrective_factors = np.clip(array_corrective_factors, 0, None)

    return array_spectra, array_peaks_to_correct, array_corrective_factors


@njit
def return_average_spectrum(array_intensity, array_unique_counts):
    """Returns intensities averaged over all pixels, given the previously computed unique m/z value
    across all pixels.

    Args:
        array_intensity (np.ndarray): Array of length n containing the sorted intensities of all the
            pixels of a given acquisition.
        array_unique_counts (np.ndarray)): Array of length m containing the unique m/z values found
            across all spectra from all pixels.

    Returns:
        np.ndarray: Array of length m containing the summed intensities for the unique m/z values
            across all spectra from all pixels.
    """
    array_unique_intensity = np.zeros(array_unique_counts.shape[0], dtype=np.float32)
    j = 0
    # For each unique m/z value, sum corresponding intensities
    for i, count in enumerate(array_unique_counts):
        array_unique_intensity[i] = np.sum(array_intensity[j : j + count])
        j += count

    return array_unique_intensity


def return_averaged_spectra_array(array):
    """Returns full spectrum averaged over all pixels

    Args:
        array (np.ndarray): Array of shape (3,n) contaning pixel index, m/z values and intensities
            in each row.

    Returns:
        np.ndarray: Array of shape (2,n) containing intensities averaged over unique m/z values
            across all pixels.
    """
    # Take the transpose for easier browsing
    array_spectra = array.T

    # Get length of spectrum (i.e. unique mz values)
    array_unique_mz, array_unique_counts = np.unique(array_spectra[1, :], return_counts=True)

    # Get averaged array
    array_unique_intensity = return_average_spectrum(array_spectra[2, :], array_unique_counts)

    return np.array([array_unique_mz, array_unique_intensity], dtype=np.float32)


def extract_raw_data(
    t_index_path,
    save=True,
    output_path="/data/lipidatlas/data/app/data/temp/",
):
    """This function loads the raw maldi data and turns it into a python friendly numpy array, along
    with a given shape for the acquisition.

    Args:
        t_index_path (tuple(int, str)): A tuple containing the index of the slice (starting from
            1)and the corresponding path for the raw data.
        save (bool, optional): If True, arrays for the extracted data are saved in a npz file.
            Defaults to True (only option implemented for now for the rest of the pipeline).
        output_path (str, optional): Path to save the output npz file. Defaults to
            "/data/lipidatlas/data/app/data/temp/".

    Returns:
        np.ndarray, np.ndarray: The first array, of shape (3,n), contains, for the current
            acquisition, the mz value (2nd column) and intensity (3rd column) for each pixel
            (first column). The second array contains two integers representing the acquisition
            shape.
    """
    try:
        # Get slice path
        slice_index = t_index_path[0]
        name = t_index_path[1]

        # Correct output path
        if "MouseBrain2" in name:
            output_path += "brain_2/"
        else:
            output_path += "brain_1/"

        # Load file in high and low resolution
        print("Loading files : " + name)
        smz_high_res = load_file(name, resolution=1e-5)
        image_shape = smz_high_res.img_shape

        # Load df with different sortings (low_res will be averaged over m/z afterwards)
        print("Creating and sorting dataframes")
        df_high_res = process_sparse_matrix(smz_high_res, sort="m/z")

        # Convert df into arrays for easier manipulation with numba
        array_high_res = df_high_res.to_numpy()

        if save:
            np.savez(
                output_path + "slice_" + str(slice_index) + "raw.npz",
                array_high_res=array_high_res,
                image_shape=image_shape,
            )

        return array_high_res, image_shape
    except:
        return None


def process_raw_data(
    t_index_path,
    save=True,
    return_result=False,
    output_path="/data/lipidatlas/data/app/data/temp/",
    load_from_file=True,
):
    """This function has been implemented to allow the parallelization of slice processing. It turns
    the MALDI data into several numpy arrays and lookup tables:
    - array_pixel_indexes_high_res: A numpy array of shape (n,2), it maps each pixel to two
        array_spectra_high_res indices, delimiting the corresponding spectrum.
    - array_spectra_high_res: A numpy array of shape (2,m), it contains the concatenated spectra of
        each pixel. First row contains the m/z values, while second row contains the corresponding
        intensities.
    - array_averaged_mz_intensity_low_res: A numpy array of shape (2, k), it contains the
        low-resolution spectrum averaged over all pixels. First row contains the m/z values, while
        second row contains the corresponding intensities.
    - array_averaged_mz_intensity_high_res: Same as array_averaged_mz_intensity_low_res, but in
        higher resolution, with, therefore, a different shape.
    - array_averaged_mz_intensity_high_res_after_standardization: Same as
        array_averaged_mz_intensity_high_res, but before applying MAIA standardization.
    - image_shape: a tuple of integers, indicating the vertical and horizontal sizes of the
        corresponding slice.
    - array_peaks_corrected: A two-dimensional array containing the peak annotations (min peak,
        max peak, average value of the peak), sorted by min_mz, but only for the lipids that
        have been transformed.
    - array_corrective_factors: A three-dimensional numpy array equal to the ratio of
        'arrays_after_transfo' and 'arrays_before_transfo' containing the corrective factor used for
        lipid (first dimension) and each pixel (second and third dimension).

    Args:
        t_index_path (tuple(int, str)): A tuple containing the index of the slice (starting from 1)
            and the corresponding path for the raw data.
        save (bool, optional): If True, output arrays are saved in a npz file. Defaults to True.
        return_result (bool, optional): If True, output arrays are returned by the function.
            Defaults to False.
        output_path (str, optional): Path to save the output npz file. Defaults to
            "/data/lipidatlas/data/app/data/temp/".
        load_from_file(bool, optional): If True, loads the extracted data from npz file. Only option
            implemented for now.
        sample_app (bool, optional): If True, the output arrays only consist of the MAIA-transformed
            lipids. Defaults to False.


    Returns:
        Depending on 'return result', returns either nothing, either several np.ndarrays, described
            above.
    """

    if load_from_file:
        # Get slice path
        slice_index = t_index_path[0]
        name = t_index_path[1]

        # Correct output path
        if "MouseBrain2" in name:
            output_path += "brain_2/"
            brain_1 = False
        else:
            output_path += "brain_1/"
            brain_1 = True

        path = output_path + "slice_" + str(slice_index) + "raw.npz"
        npzfile = np.load(path)
        # Load individual arrays
        array_high_res = npzfile["array_high_res"]
        image_shape = npzfile["image_shape"]
    else:
        raise Exception("Loading from arguments is not implemented yet")

    print("Compute and normalize pixels values according to TIC")
    # Get the TIC per pixel for normalization (must be done before filtering out peaks)
    array_TIC = compute_TIC_per_pixel(array_high_res, image_shape[0] * image_shape[1])
    array_high_res = normalize_per_TIC_per_pixel(array_high_res, array_TIC)

    # Filter out the non-requested peaks and convert to array
    print("Filtering out noise and matrix peaks")

    # Get the peak annotation file
    array_peaks = load_peak_file(name)

    # Get the list of m/z values to keep for visualization
    array_mz_lipids = load_lipid_file(
        slice_index - 10 if not brain_1 else slice_index,
        path="data/annotations/df_match_brain_2.csv"
        if not brain_1
        else "data/annotations/df_match_brain_1.csv",
    )

    # Get the arrays to standardize data with MAIA
    (
        l_lipids_str,
        l_lipids_float,
        arrays_before_transfo,
        arrays_after_transfo,
    ) = get_standardized_values(
        slice_index - 10 if not brain_1 else slice_index,
        path_array_data="/data/lipidatlas/data/processed/brain1/BRAIN1"
        if brain_1
        else "/data/lipidatlas/data/processed/brain2/BRAIN2",
        path_array_transformed_data="/data/lipidatlas/data/processed/brain1/BRAIN1_normalized"
        if brain_1
        else "/data/lipidatlas/data/processed/brain2/BRAIN2_normalized",
    )

    if SAMPLE_APP:
        l_lipids_str = l_lipids_str[:N_SAMPLES]
        l_lipids_float = l_lipids_float[:N_SAMPLES]
        arrays_before_transfo = arrays_before_transfo[:N_SAMPLES]
        arrays_after_transfo = arrays_after_transfo[:N_SAMPLES]

    # Get the array of MAIA-transformed lipids
    array_peaks_MAIA = get_array_peaks_to_correct(
        l_lipids_float, array_mz_lipids, array_peaks, slice_index=slice_index - 10
    )

    # Filter out all the undesired values
    l_to_keep_high_res, l_mz_lipids_kept = filter_peaks(
        array_high_res, array_peaks_MAIA if SAMPLE_APP else array_peaks, array_mz_lipids[:, 0]
    )

    # Keep only the requested peaks
    array_high_res = array_high_res[l_to_keep_high_res]

    print("Prepare data for standardization")
    # Double sort by pixel and mz
    array_high_res = array_high_res[
        np.lexsort((array_high_res[:, 1], array_high_res[:, 0]), axis=0)
    ]
    # Get arrays spectra and corresponding array_pixel_index tables for the high res
    array_pixel_high_res = array_high_res[:, 0].T.astype(np.int32)
    array_pixel_indexes_high_res = return_array_pixel_indexes(
        array_pixel_high_res, image_shape[0] * image_shape[1]
    )

    print("Standardize data")
    # Standardize a copy of a the data
    (
        array_high_res_standardized,
        array_peaks_corrected,
        array_corrective_factors,
    ) = standardize_values(
        array_high_res.copy(),
        array_pixel_indexes_high_res,
        array_peaks,
        array_mz_lipids,
        l_lipids_float,
        arrays_before_transfo,
        arrays_after_transfo,
        array_peaks_MAIA,
        ignore_standardization=False if len(l_lipids_str) > 0 else True,
    )

    # Sort according to mz for averaging
    print("Sorting by m/z value for averaging")
    array_high_res = array_high_res[np.lexsort((array_high_res[:, 1],), axis=0)]

    # Average low/high resolution arrays over identical mz across pixels
    print("Getting spectrums array averaged accross pixels")
    array_averaged_mz_intensity_high_res = return_averaged_spectra_array(array_high_res)

    print("Build the low-resolution averaged array from the high resolution averaged array")
    array_averaged_mz_intensity_low_res = reduce_resolution_sorted_array_spectra(
        array_averaged_mz_intensity_high_res, resolution=10**-2
    )

    # Same with the standardized data
    print("Sorting by m/z value for averaging after standardization")
    array_high_res_standardized = array_high_res_standardized[
        np.lexsort((array_high_res_standardized[:, 1],), axis=0)
    ]

    # Average low/high resolution arrays over identical mz across pixels
    print("Getting spectrums array averaged accross pixels")
    array_averaged_mz_intensity_high_res_after_standardization = return_averaged_spectra_array(
        array_high_res_standardized
    )

    # Process more high-resolution data
    print("Double sorting according to pixel and mz high-res array")
    array_high_res = array_high_res[
        np.lexsort((array_high_res[:, 1], array_high_res[:, 0]), axis=0)
    ]

    # Get arrays spectra and corresponding array_pixel_index tables for the high resolution
    print("Getting corresponding spectra arrays")
    array_pixel_high_res = array_high_res[:, 0].T.astype(np.int32)
    array_spectra_high_res = array_high_res[:, 1:].T.astype(np.float32)
    array_pixel_indexes_high_res = return_array_pixel_indexes(
        array_pixel_high_res, image_shape[0] * image_shape[1]
    )

    # Save all array as a npz file as a temporary backup
    if save:
        print("Saving : " + name)
        np.savez(
            output_path + "slice_" + str(slice_index) + ".npz",
            array_pixel_indexes_high_res=array_pixel_indexes_high_res,
            array_spectra_high_res=array_spectra_high_res,
            array_averaged_mz_intensity_low_res=array_averaged_mz_intensity_low_res,
            array_averaged_mz_intensity_high_res=array_averaged_mz_intensity_high_res,
            array_averaged_mz_intensity_high_res_after_standardization=array_averaged_mz_intensity_high_res_after_standardization,
            image_shape=image_shape,
            array_peaks_corrected=array_peaks_corrected,
            array_corrective_factors=array_corrective_factors,
        )

    # Returns all array if needed
    if return_result:
        return (
            array_pixel_indexes_high_res,
            array_spectra_high_res,
            array_averaged_mz_intensity_low_res,
            array_averaged_mz_intensity_high_res,
            array_averaged_mz_intensity_high_res_after_standardization,
            image_shape,
            array_peaks_corrected,
            array_corrective_factors,
        )
