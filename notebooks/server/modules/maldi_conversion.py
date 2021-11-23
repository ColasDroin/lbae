###### IMPORT MODULES ######

# Standard imports
import numpy as np
from numba import njit
import os
import pandas as pd

# Homemade packages
from lbae.modules.tools.mspec import SmzMLobj
from lbae.modules.tools.spectra import reduce_resolution_sorted_array_spectra

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


def load_peak_file(path):
    """This function loads the peaks annotations from a csv file located at the provided path. 
    It returns a dataframe sorted by peak value (m/z) annotation.

    Args:
        path (string): The path of the csv file containing the peaks annotations.

    Returns:
        pandas.dataframe: The sorted dataframe containing the annotations.
    """
    # Try to load the peaks annotations using the first definition used for the csv file
    try:
        df = pd.read_csv(path + ".csv", sep="\t")

        # Drop the columns that we won't use afterwards
        df = df.drop(
            [
                "Unnamed: 0",
                "pixel_max_hits",
                "percent_1_hit",
                "concentration",
                "median_intensity",
                "tissue",
                "mz_estimated",
                "difference",
                "matrix",
            ],
            axis=1,
        )
    except:

        # Try an alternative definition
        try:
            df = pd.read_csv(path + ".csv", sep=",")

            # Drop the columns that we won't use afterwards
            df = df.drop(
                [
                    "Unnamed: 0",
                    "pixel_max_hits",
                    "percent_1_hit",
                    "concentration",
                    "median_intensity",
                    "tissue",
                    "mz_estimated",
                    "difference",
                    "matrix",
                ],
                axis=1,
            )
        except:

            # Try last possible definition
            df = pd.read_csv(path + ".csv", sep=",")

            # Drop the columns that we won't use afterwards
            df = df.drop(
                [
                    "Unnamed: 0",
                    "pixel_max_hits",
                    "percent_1_hit",
                    "concentration",
                    "median_intensity",
                    "mz_estimated",
                    "difference",
                ],
                axis=1,
            )

    # Sort by increasing m/z annotation for the peaks
    df = df.sort_values(by="min", axis=0)
    return df


def process_sparse_matrix(smz, sort=["Pixel", "m/z"], sample=False):
    """This function converts the space matrix into a dataframe sorted according to the 'sort' parameter.
    It is possible to work only on a tiny subset of the matrix with the 'sample' parameter for debugging purposes. 

    Args:
        smz (scipy.sparse): The sparse matrix obtained from the MALDI imaging.
        sort (list, optional): A list of column names according to which the final dataframe should be sorted. 
            Defaults to ["Pixel", "m/z"].
        sample (bool, optional): A boolean parameter to sample only a subset of the matrix. Defaults to False.

    Returns:
        pandas.Dataframe: A sorted dataframe with three columns: pixels index, m/z, and intensity value.
    """
    # We're going to slice the matrix row by row, so it's faster to convert it to csr rather than csc
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
def filter_peaks(array_spectra, array_peaks, verbose=False):
    """This function is used to filter out all the spectrum data in 'array_spectra' that 
    has not been annotated as peak in 'array_peaks'.

    Args:
        array_spectra (np.ndarray): A numpy array containing spectrum data (pixel index, m/z and intensity).
        array_peaks (numpy.ndarray): A numpy array containing the peak annotations.
        verbose (bool): If True, some prints are displayed for debugging purposes. Default to False.

    Returns:
        list: m/z values corresponding to peaks that have been annotated.
    """
    # Define initial values
    l_to_keep = []
    index_peak = 0
    idx_curr_mz = 0
    l_n_pix = []

    # Need to initialize the set with an int inside and then delete it because numba is retarded
    set_pix = {0}
    set_pix.remove(0)

    while idx_curr_mz < array_spectra.shape[0] and index_peak < array_peaks.shape[0]:
        idx_pix, mz, intensity = array_spectra[idx_curr_mz]
        min_mz, max_mz, n_pix = array_peaks[index_peak]

        if idx_pix == 0 and verbose:
            print("idx_pix is 0")
            print("mz, intensity, min_mz, max_mz, n_pix", mz, intensity, min_mz, max_mz, n_pix)

        # Either we are before the current window
        if mz <= min_mz:
            idx_curr_mz += 1

        # Either current mz is in the current window
        elif mz > min_mz and mz < max_mz:
            l_to_keep.append(idx_curr_mz)
            set_pix.add(idx_pix)
            idx_curr_mz += 1

        # Either we're beyond, in which cas we move the window, and record the number of unique pixels
        # in the window for later check
        else:
            index_peak += 1
            l_n_pix.append(len(set_pix))
            set_pix.clear()

    # Check that the pixel recorded are identical to the expected number of pixels recorded
    if verbose:
        print("Difference between number of recorded pixels", np.sum(np.array(l_n_pix) - array_peaks[:, 2]))
        print(np.array(l_n_pix)[-10:])
        print(array_peaks[-10:, 2])

    return l_to_keep


@njit
def return_array_pixel_indexes(array_pixel, total_shape):
    """Returns an array of pixel indexes: for each pixel (corresponding to the index of a given row of 
    array_pixel_indexes), it returns the 2 boundaries in the corresponding array_spectra (upper boundarie is included).

    Args:
        array_pixel (np.ndarray): Array of length n containing the index of each pixel for each m/z value.
        total_shape (int): Total number of pixels in the slice.

    Returns:
        np.ndarray: An array of shape (m,2) containing the boundary indices of each pixel in the original spectra array. 
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


@njit
def return_average_spectrum(array_intensity, array_unique_counts):
    """Returns intensities averaged over all pixels, given the previously computed unique m/z value across all pixels.

    Args:
        array_intensity (np.ndarray): Array of length n containing the sorted intensities of all the pixels of a a
            given acquisition. 
        array_unique_counts (np.ndarray)): Array of length m containing the unique m/z values found across all spectra
            from all pixels.

    Returns:
        np.ndarray: Array of length m containing the summed intensities for the unique m/z values across all spectra
            from all pixels.
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
        array (np.ndarray): Array of shape (3,n) contaning pixel index, m/z values and intensities in each row. 

    Returns:
        np.ndarray: Array of shape (2,n) containing intensities averaged over unique m/z values across all pixels.
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
    bool_filter_peaks=True,
    save=True,
    return_result=False,
    output_path="notebooks/server/data/temp/",
    verbose=True,
):
    """This function has been implemented to allow the paralellization of slice processing. It turns the raw MALDI data
    into several numpy arrays and lookup tables:
    - array_pixel_indexes_high_res: of shape (n,2), it maps each pixel to two array_spectra_high_res indices, delimiting
      the corresponding spectrum.
    - array_spectra_high_res: of shape (2,m), it contains the concatenated spectra of each pixel. First row contains the
      m/z values, while second row contains the corresponding intensities.
    - array_averaged_mz_intensity_low_res: of shape (2, k), it contains the low-resolution spectrum averaged over all 
      pixels. First row contains the m/z values, while second row contains the corresponding intensities.
    - array_averaged_mz_intensity_high_res: Same as array_averaged_mz_intensity_low_res, but in higher resolution, with,
      therefore, a different shape.
    - image_shape: a tuple of integers, indicating the vertical and horizontal sizes of the corresponding slice.

    Args:
        t_index_path (tuple(int, str)): A tuple containing the index of the slice (starting from 1) and the 
            corresponding path for the raw data.
        bool_filter_peaks (bool, optional): If True, non-annotated peaks are filtered out. Defaults to True.
        save (bool, optional): If True, output arrays are saved in a npz file. Defaults to True.
        return_result (bool, optional): If True, output arrays are returned by the function. Defaults to False.
        output_path (str, optional): Path to save the output npz file. Defaults to "notebooks/server/data/temp/".
        verbose (bool, optional): If True, print the successive steps used for the conversion of the raw data. 
            Defaults to True.

    Returns:
        Depending on 'return result', returns either nothing, either several np.ndarrays, described above.
    """
    # Get slice path
    index_slice = t_index_path[0]
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

    # Filter out the non-requested peaks and convert to array
    appendix = "_unfiltered"
    if bool_filter_peaks:
        try:
            df_peaks = load_peak_file(name)
            array_peaks = df_peaks.to_numpy()
            l_to_keep_high_res = filter_peaks(array_high_res, array_peaks)
            array_high_res = array_high_res[l_to_keep_high_res]
            appendix = "_filtered"
        except:
            appendix = "_unfiltered"

    # Average low/high resolution arrays over identical mz across pixels
    print("Getting spectrums array averaged accross pixels")
    array_averaged_mz_intensity_high_res = return_averaged_spectra_array(array_high_res)

    print("Build the low-resolution averaged array from the high resolution averaged array")
    array_averaged_mz_intensity_low_res = reduce_resolution_sorted_array_spectra(
        array_averaged_mz_intensity_high_res, resolution=10 ** -2
    )

    # Process more high-resolution data
    print("Double sorting high-res array")
    array_high_res = array_high_res[np.lexsort((array_high_res[:, 1], array_high_res[:, 0]), axis=0)]

    # Get arrays spectra and corresponding array_pixel_index tables for the high resolution
    print("Getting corresponding spectra arrays")
    array_pixel_high_res = array_high_res[:, 0].T.astype(np.int32)
    array_spectra_high_res = array_high_res[:, 1:].T.astype(np.float32)
    array_pixel_indexes_high_res = return_array_pixel_indexes(array_pixel_high_res, image_shape[0] * image_shape[1])

    # Save all array as a npz file as a temporary backup
    if save:
        print("Saving : " + name)
        if len(t_index_path) > 2:
            np.savez(
                output_path + "slice_" + str(index_slice) + "_bis" + appendix + ".npz",
                array_pixel_indexes_high_res=array_pixel_indexes_high_res,
                array_spectra_high_res=array_spectra_high_res,
                array_averaged_mz_intensity_low_res=array_averaged_mz_intensity_low_res,
                array_averaged_mz_intensity_high_res=array_averaged_mz_intensity_high_res,
                image_shape=image_shape,
            )

        else:
            np.savez(
                output_path + "slice_" + str(index_slice) + appendix + ".npz",
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

