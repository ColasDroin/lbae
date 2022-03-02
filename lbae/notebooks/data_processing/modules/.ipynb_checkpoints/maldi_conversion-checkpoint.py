###### IMPORT MODULES ######

# Standard modules
import numpy as np
from numba import njit
import os
import pandas as pd

# Homemade packages
from modules.tools.mspec import SmzMLobj
from modules.tools.spectra import reduce_resolution_sorted_array_spectra

###### DEFINE UTILITY FUNCTIONS ######
def load_file(path, resolution=1e-5):
    """This function loads the specified MALDI file from the raw data format (.mzML and .UDP) 
    with the given resolution, and turns it into a scipy sparse matrix. 

    Args:
        path (string): The path of the file to load.
        resolution (float, optional): The resolution of the file to load. Defaults to 1e-5.

    Returns:
        scipy.sparse: A sparse matrix containing the intensity for each m/z value.
    """
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


def load_peak_file(path):
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
    return df.to_numpy()


def load_lipid_file(section_index, path):
    """This function loads a set of specific lipid annotations containing a molecule ID, the average 
    mz for the molecule, the section index and potentially other information, from a csv file 
    located at the provided path. It returns an array of mz values corresponding to the lipids we 
    want to keep for further visualization.

    Args:
        section_index (int): The index of the current acquisition (first slice having index 1).
        path (string): The path of the csv file containing the lipids annotations.

    Returns:
        np.ndarray: A unidimensional array of m/z values corrsponding to the lipids that we want to
            keep for further visualization.
    """
    # Load the peaks annotations using the last definition used for the csv file
    df = pd.read_csv(path, sep=",")

    # Drop the columns that we won't use afterwards
    df = df.drop(["molecule_ID", "concentration", "mz_estimated_total",], axis=1,)

    # Keep only the current section
    df = df[df["section_ix"] == section_index - 1]

    # Return a numpy array of mz values
    return np.sort(np.array(df["mz_estimated"], dtype=np.float32))


@njit
def filter_peaks(array_spectra, array_peaks, array_mz_lipids):
    """This function is used to filter out all the spectrum data in 'array_spectra' that 
    has not been annotated as peak in 'array_peaks' and that do not belong to 'array_mz_lipids'.

    Args:
        array_spectra (np.ndarray): A numpy array containing spectrum data (pixel index, m/z and 
            intensity), sorted by mz (but not necessarily by pixel index).
        array_peaks (np.ndarray): A numpy array containing the peak annotations (min peak, max peak, 
            number of pixels containing the peak, average value of the peak), sorted by min_mz.
        array_mz_lipids (np.ndarray): A 1-D numpy array containing the mz values of the lipids we 
            want to visualize.

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
    mz_lipid = array_mz_lipids[idx_lipid]
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
            while mz_lipid < min_mz and idx_lipid < array_mz_lipids.shape[0]:
                idx_lipid += 1
                mz_lipid = array_mz_lipids[idx_lipid]

            # If we've explored all lipids already, exit the loop
            if idx_lipid == array_mz_lipids.shape[0]:
                break

            # If mz lipid is not in the current peak, move on to the next
            if mz_lipid > max_mz or np.abs(mz_estimated - mz_lipid) > 2 * 10 ** -4:
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
    # * array_mz_lipids as argument in the function, but it should still work if molecules not
    # * belonging to array_mz_lipids are not excluded
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
    path_array_data="/data/lipidatlas/data/processed/BRAIN1",
    path_array_transformed_data="/data/lipidatlas/data/processed/BRAIN1_normalized",
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
    for lipid_str in l_lipids_str:
        array_before_transfo = np.load(
            path_array_data + "/" + lipid_str + "/" + str(slice_index - 1) + ".npy"
        )
        array_after_transfo = np.load(
            path_array_transformed_data + "/" + lipid_str + "/" + str(slice_index - 1) + ".npy"
        )
        l_arrays_before_transfo.append(array_before_transfo)
        l_arrays_after_transfo.append(array_after_transfo)
    return (
        l_lipids_str,
        l_lipids_float,
        np.array(l_arrays_before_transfo, dtype=np.float32),
        np.array(l_arrays_after_transfo, dtype=np.float32),
    )


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
    min_mz, max_mz, n_pix, mz_estimated = array_peaks[idx_peak]
    while idx_mz < array_spectra_pixel.shape[0] and idx_peak < array_peaks.shape[0]:
        idx_pix, mz, intensity = array_spectra_pixel[idx_mz]

        # new window has been discovered
        if mz >= min_mz:
            idx_min_mz = idx_mz
            while mz <= max_mz:
                idx_mz += 1
                idx_pix, mz, intensity = array_spectra_pixel[idx_mz]
            idx_max_mz = idx_mz - 1

            # Compute intensities of the window before and after correction
            if idx_peak < len(arrays_before_transfo):
                intensity_before = arrays_before_transfo[idx_peak].flatten()[idx_pixel]
                intensity_after = arrays_after_transfo[idx_peak].flatten()[idx_pixel]

                # Most likely, the annotation doesn't exist, so insert it
                if idx_max_mz == idx_min_mz or idx_max_mz == idx_min_mz - 1:
                    pass
                    # array_spectra_pixel = np.insert(array_spectra_pixel, idx_min_mz,
                    #   [idx_pix, mz_estimated, intensity_after], axis = 0)
                # Else compute a multiplicative factor
                else:

                    # Compute sum of expression between limits
                    integral = np.sum(array_spectra_pixel[idx_min_mz : idx_max_mz + 1, 2])

                    # Assess that this sum is equal to the one precomputed with MAIA
                    if np.abs(integral - intensity_before) > 10 ** -4:
                        print("There seems to be a problem with the computation of the integral")
                        print(integral, intensity_before)
                        print(idx_min_mz, idx_max_mz)
                    # else:
                    #     print("ok")

                    correction = intensity_after / intensity_before

                    # Multiply all intensities in the window by the corrective coefficient
                    array_spectra_pixel[idx_min_mz : idx_max_mz + 1, 2] *= correction

                # Move on to the next peak
                idx_peak += 1
            else:
                raise Exception(
                    "There seems to be more peaks than lipids annotated... Exiting function"
                )
        else:
            idx_mz += 1

    return array_spectra_pixel


def standardize_values(
    array_spectra,
    array_pixel_indexes,
    array_peaks,
    l_lipids_float,
    arrays_before_transfo,
    arrays_after_transfo,
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
        l_lipids_float (list): A list containing the estimated m/z values of the lipids we want to 
            visualize.
        arrays_before_transfo (np.ndarray): A numpy array of shape (n_lipids, image_shape[0], 
            image_shape[1]) containing the cumulated intensities (summed over all bins) of the 
            lipids we want to visualize, for each pixel, before these intensities were transformed.
        arrays_after_transfo (np.ndarray): A numpy array of shape (n_lipids, image_shape[0], 
            image_shape[1]) containing the cumulated intensities (summed over all bins) of the 
            lipids we want to visualize, for each pixel, after these intensities were transformed.
    Returns:
        np.ndarray: A numpy array containing spectrum data (pixel index, m/z and intensity), sorted 
            by pixel index and mz, with lipids values transformed.
    """

    def compute_number_peaks_lipid_annotation(array_peaks, l_lipids_float, precision=14 * 10 ** -4):
        # keep only the peak annotation that correspond to the lipids which have been transformed
        rows_to_keep = []
        for idx, [mini, maxi, npix, mz_est] in enumerate(array_peaks):
            for mz_lipid in l_lipids_float:
                # Problem with this precision... Which slice must taken to compute mz_estimated?
                if np.abs(mz_est - mz_lipid) <= precision:
                    rows_to_keep.append(idx)
                    break
        return rows_to_keep

    for factor_precision in range(20):
        rows_to_keep = compute_number_peaks_lipid_annotation(
            array_peaks, l_lipids_float, precision=factor_precision * 10 ** -4
        )
        if len(rows_to_keep) == len(l_lipids_float):
            break
    array_peaks_to_correct = array_peaks[rows_to_keep]

    # new_array_spectra = []
    for idx_pixel, [idx_pixel_min, idx_pixel_max] in enumerate(array_pixel_indexes):
        array_spectra_pixel = array_spectra[idx_pixel_min : idx_pixel_max + 1]

        if len(array_spectra_pixel) > 1:
            array_spectra_pixel = compute_standardization(
                array_spectra_pixel,
                idx_pixel,
                array_peaks_to_correct,
                arrays_before_transfo,
                arrays_after_transfo,
            )

            # Reattribute the corrected values to the intial spectrum
            array_spectra[idx_pixel_min : idx_pixel_max + 1] = array_spectra_pixel
        # new_array_spectra.append(array_spectra_pixel)

    return array_spectra  # np.array(new_array_spectra)


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


def process_raw_data(
    t_index_path,
    do_filter_peaks=True,
    standardize_lipid_values=True,
    save=True,
    return_result=False,
    output_path="notebooks/data_processing/data/temp/",
):
    """This function has been implemented to allow the parallelization of slice processing. It turns 
    the raw MALDI data into several numpy arrays and lookup tables:
    - array_pixel_indexes_high_res: of shape (n,2), it maps each pixel to two array_spectra_high_res 
        indices, delimiting the corresponding spectrum.
    - array_spectra_high_res: of shape (2,m), it contains the concatenated spectra of each pixel. 
        First row contains the m/z values, while second row contains the corresponding intensities.
    - array_averaged_mz_intensity_low_res: of shape (2, k), it contains the low-resolution spectrum 
        averaged over all pixels. First row contains the m/z values, while second row contains the 
        corresponding intensities.
    - array_averaged_mz_intensity_high_res: Same as array_averaged_mz_intensity_low_res, but in 
        higher resolution, with, therefore, a different shape.
    - image_shape: a tuple of integers, indicating the vertical and horizontal sizes of the 
        corresponding slice.

    Args:
        t_index_path (tuple(int, str)): A tuple containing the index of the slice (starting from 1) 
            and the corresponding path for the raw data.
        do_filter_peaks (bool, optional): If True, non-annotated peaks are filtered out. Defaults to 
            True.
        standardize_lipid_values (bool, optional): If True, the lipid intensities that have been 
            through the MAIA pipeline will be standardized across slices. Defaults to True.
        save (bool, optional): If True, output arrays are saved in a npz file. Defaults to True.
        return_result (bool, optional): If True, output arrays are returned by the function. 
            Defaults to False.
        output_path (str, optional): Path to save the output npz file. Defaults to 
            "notebooks/data_processing/data/temp/".


    Returns:
        Depending on 'return result', returns either nothing, either several np.ndarrays, described 
            above.
    """
    # Get slice path
    slice_index = t_index_path[0]
    name = t_index_path[1]

    # Load file in high and low resolution
    print("Loading files : " + name)
    smz_high_res = load_file(name, resolution=1e-5)
    image_shape = smz_high_res.img_shape

    # Load df with different sortings (low_res will be averaged over m/z afterwards)
    print("Creating and sorting dataframes")
    df_high_res = process_sparse_matrix(smz_high_res, sort="m/z")

    # Convert df into arrays for easier manipulation with numba
    array_high_res = df_high_res.to_numpy()

    print("Compute and normalize pixels values according to TIC")
    # Get the TIC per pixel for normalization (must be done before filtering out peaks)
    array_TIC = compute_TIC_per_pixel(array_high_res, image_shape[0] * image_shape[1])
    array_high_res = normalize_per_TIC_per_pixel(array_high_res, array_TIC)

    # Filter out the non-requested peaks and convert to array
    appendix = "_unfiltered"
    if do_filter_peaks:
        print("Filtering out noise and matrix peaks")
        try:
            # Get the peak annotation file
            array_peaks = load_peak_file(name)
            # Get the list of m/z values to keep for visualization
            array_mz_lipids = load_lipid_file(1, path="data/annotations/df_match.csv")
            # Filter out all the undesired values
            l_to_keep_high_res, l_mz_lipids_kept = filter_peaks(
                array_high_res, array_peaks, array_mz_lipids
            )
            # Keep only the annotated peaks
            array_high_res = array_high_res[l_to_keep_high_res]
            if standardize_lipid_values:
                # Double sort by pixel and mz
                array_high_res = array_high_res[
                    np.lexsort((array_high_res[:, 1], array_high_res[:, 0]), axis=0)
                ]
                # Get arrays spectra and corresponding array_pixel_index tables for the high res
                array_pixel_high_res = array_high_res[:, 0].T.astype(np.int32)
                array_pixel_indexes_high_res = return_array_pixel_indexes(
                    array_pixel_high_res, image_shape[0] * image_shape[1]
                )
                (
                    l_lipids_str,
                    l_lipids_float,
                    arrays_before_transfo,
                    arrays_after_transfo,
                ) = get_standardized_values(slice_index)
                array_high_res = standardize_values(
                    array_high_res,
                    array_pixel_indexes_high_res,
                    array_peaks,
                    l_lipids_float,
                    arrays_before_transfo,
                    arrays_after_transfo,
                )
                appendix = "_filtered"
        except:
            appendix = "_unfiltered"

    # Sort according to mz for averaging
    print("Sorting by m/z value for averaging")
    array_high_res = array_high_res[np.lexsort((array_high_res[:, 1],), axis=0)]

    # Average low/high resolution arrays over identical mz across pixels
    print("Getting spectrums array averaged accross pixels")
    array_averaged_mz_intensity_high_res = return_averaged_spectra_array(array_high_res)

    print("Build the low-resolution averaged array from the high resolution averaged array")
    array_averaged_mz_intensity_low_res = reduce_resolution_sorted_array_spectra(
        array_averaged_mz_intensity_high_res, resolution=10 ** -2
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
        if len(t_index_path) > 2:
            np.savez(
                output_path + "slice_" + str(slice_index) + "_bis" + appendix + ".npz",
                array_pixel_indexes_high_res=array_pixel_indexes_high_res,
                array_spectra_high_res=array_spectra_high_res,
                array_averaged_mz_intensity_low_res=array_averaged_mz_intensity_low_res,
                array_averaged_mz_intensity_high_res=array_averaged_mz_intensity_high_res,
                image_shape=image_shape,
            )

        else:
            np.savez(
                output_path + "slice_" + str(slice_index) + appendix + ".npz",
                array_pixel_indexes_high_res=array_pixel_indexes_high_res,
                array_spectra_high_res=array_spectra_high_res,
                array_averaged_mz_intensity_low_res=array_averaged_mz_intensity_low_res,
                array_averaged_mz_intensity_high_res=array_averaged_mz_intensity_high_res,
                image_shape=image_shape,
            )

    # Returns all array if needed
    if return_result:
        return (
            array_pixel_indexes_high_res,
            array_spectra_high_res,
            array_averaged_mz_intensity_low_res,
            array_averaged_mz_intensity_high_res,
            image_shape,
        )

