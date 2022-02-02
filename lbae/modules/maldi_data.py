###### IMPORT MODULES ######

# Standard imports
import pickle
import numpy as np
import pandas as pd
from lbae.modules.tools.misc import logmem
import logging

###### DEFINE MaldiData CLASS ######


class MaldiData:
    """
    A class to access the various arrays in the dataset from two dictionnaries, lightweight (always kept in ram), and 
    memmap (remains on disk). It uses the special attribute __slots__ for faster access to the attributes.

    Attributes:
        _dic_lightweight (dictionnary): a dictionnary containing the following lightweights arrays, 
            which therefore remain in memory as long as the app is running:
            - image_shape: a tuple of integers, indicating the vertical and horizontal sizes of the 
                corresponding slice.
            - divider_lookup: integer that sets the resolution of the lookup tables.
            - array_avg_spectrum_downsampled: bidimensional, it contains the low-resolution spectrum averaged over all 
                pixels. First row contains the m/z values, while second row contains the corresponding intensities.
            - array_lookup_pixels: bidimensional, it maps each pixel to two array_spectra_high_res indices, delimiting
                the corresponding spectrum.
            - array_lookup_mz_avg: unidimensional, it maps m/z values to indexes in the averaged 
                array_spectra for each pixel.
            In addition, it contains the shape of all the arrays stored in the numpy memory maps.
        _dic_memmap (dictionnary): a dictionnary containing numpy memory maps allowing to access the heavyweights 
            arrays of the datasets, without saturating the disk. The arrays in the dictionnary are:
            - array_spectra: bidimensional, it contains the concatenated spectra of each pixel. First row contains the
                m/z values, while second row contains the corresponding intensities.
            - array_avg_spectrum: bidimensional, it contains the high-resolution spectrum averaged over all 
                pixels. First row contains the m/z values, while second row contains the corresponding intensities.
            - array_lookup_mz: bidimensional, it maps m/z values to indexes in array_spectra for each pixel.
            - array_cumulated_lookup_mz_image: bidimensional, it maps m/z values to the cumulated spectrum until the 
                corresponding m/z value for each pixel.
        _n_slices (int): number of slices present in the dataset.
        _df_annotations (pd.dataframe): a dataframe containing for each slice and each annotated peak the name of 
            the lipid inbetween the two annotated peak boundaries.
        _path_data (str): path were the data files are stored.

    Methods:
        get_annotations(): getter for the lipid annotation of each slice, contained in a pandas dataframe.
        get_slice_number(): getter for the number of slices present in the dataset.
        get_image_shape(slice_index): getter for image_shape, which indicates the shape of the image corresponding to 
            the acquisition indexed by slice_index.
        get_divider_lookup(slice_index): getter for divider_lookup, which sets the resolution of the lookup of the 
            acquisition indexed by slice_index.
        get_array_avg_spectrum_downsampled(slice_index): getter for array_avg_spectrum_downsampled, which is a lookup 
            table for the low-resolution average spectrum of the acquisition indexed by slice_index.
        get_array_lookup_pixels(slice_index):
        get_array_lookup_mz_avg(slice_index):
        get_array_spectra(slice_index):
        get_array_mz(slice_index):
        get_array_intensity(slice_index):
        get_array_avg_spectrum(slice_index):
        get_array_lookup_mz(slice_index):
        get_array_cumulated_lookup_mz_image(slice_index):
        get_partial_array_spectra(slice_index, lb=None, hb=None, index=None):
        get_partial_array_mz(slice_index, lb=None, hb=None, index=None):
        get_partial_array_intensity(slice_index, lb=None, hb=None, index=None):
        get_partial_array_avg_spectrum(slice_index, lb=None, hb=None):
        get_lookup_mz(slice_index, index):
        get_cumulated_lookup_mz_image(slice_index, index):
    """

    __slots__ = ["_dic_lightweight", "_dic_memmap", "_n_slices", "_df_annotations", "_path_data"]

    def __init__(self, path_data="lbae/data/whole_dataset/", path_annotations="lbae/data/annotations/"):

        logging.info("Initializing MaldiData object" + logmem())

        # Load the dictionnary containing small-size data for all slices
        with open(path_data + "light_arrays.pickle", "rb") as handle:
            self._dic_lightweight = pickle.load(handle)

        # Simple variable to get the number of slices
        self._n_slices = len(self._dic_lightweight)

        # Set the accesser to the mmap files
        self._dic_memmap = {}
        for slice_index in range(1, self._n_slices + 1):
            self._dic_memmap[slice_index] = {}
            for array_name in [
                "array_spectra",
                "array_avg_spectrum",
                "array_lookup_mz",
                "array_cumulated_lookup_mz_image",
            ]:
                self._dic_memmap[slice_index][array_name] = np.memmap(
                    path_data + array_name + "_" + str(slice_index) + ".mmap",
                    dtype="float32" if array_name != "array_lookup_mz" else "int32",
                    mode="r",
                    shape=self._dic_lightweight[slice_index][array_name + "_shape"],
                )

        # Save path_data for cleaning memmap in case
        self._path_data = path_data

        # Load lipid annotation (not user-session specific)
        self._df_annotations = pd.read_csv(path_annotations + "lipid_annotation.csv")
        self._df_annotations["name"] = self._df_annotations["name"].map(lambda x: x.split("_")[1])

        # Build a list of lipid names for faster access and numba manipulation

    def get_annotations(self):
        return self._df_annotations

    def get_slice_number(self):
        return self._n_slices

    def get_image_shape(self, slice_index):
        return self._dic_lightweight[slice_index]["image_shape"]

    def get_divider_lookup(self, slice_index):
        return self._dic_lightweight[slice_index]["divider_lookup"]

    def get_array_avg_spectrum_downsampled(self, slice_index):
        # Previously called array_averaged_mz_intensity_low_res
        return self._dic_lightweight[slice_index]["array_avg_spectrum_downsampled"]

    def get_array_lookup_pixels(self, slice_index):
        # Previously called array_pixel_indexes_high_res
        return self._dic_lightweight[slice_index]["array_lookup_pixels"]

    def get_array_lookup_mz_avg(self, slice_index):
        # Previously called lookup_table_averaged_spectrum_high_res
        return self._dic_lightweight[slice_index]["array_lookup_mz_avg"]

    def get_array_spectra(self, slice_index):
        # Previously called array_spectra_high_res.
        return self._dic_memmap[slice_index]["array_spectra"]

    def get_array_mz(self, slice_index):
        # Previously called array_spectra_high_res
        return self._dic_memmap[slice_index]["array_spectra"][0, :]

    def get_array_intensity(self, slice_index):
        # Previously called array_spectra_high_res
        return self._dic_memmap[slice_index]["array_spectra"][1, :]

    def get_array_avg_spectrum(self, slice_index):
        # Previously called array_averaged_mz_intensity_high_res
        return self._dic_memmap[slice_index]["array_avg_spectrum"]

    def get_array_lookup_mz(self, slice_index):
        # Previously called lookup_table_spectra_high_res
        return self._dic_memmap[slice_index]["array_lookup_mz"]

    def get_array_cumulated_lookup_mz_image(self, slice_index):
        # Previously called cumulated_image_lookup_table_high_res
        return self._dic_memmap[slice_index]["array_cumulated_lookup_mz_image"]

    def get_partial_array_spectra(self, slice_index, lb=None, hb=None, index=None):

        # If not specific index has been provided, it returns a range
        if index is None:

            # Start with most likely case
            if hb is not None and lb is not None:
                return self._dic_memmap[slice_index]["array_spectra"][:, lb:hb]

            # Second most likely case : full slice
            elif lb is None and hb is None:
                return self.get_array_intensity(slice_index)

            # Most likely the remaining cases won't be used
            elif lb is None:
                return self._dic_memmap[slice_index]["array_spectra"][:, :hb]
            else:
                return self._dic_memmap[slice_index]["array_spectra"][:, lb:]

        # Else, it returns the required index
        else:
            if lb is not None or hb is not None:
                logging.warning(
                    "Both one or several boundaries and one index have been specified when calling array_spectra. "
                    + "Only the index request will be satisfied."
                )
            return self._dic_memmap[slice_index]["array_spectra"][:, index]

    def get_partial_array_mz(self, slice_index, lb=None, hb=None, index=None):

        # If not specific index has been provided, it returns a range
        if index is None:

            # Start with most likely case
            if hb is not None and lb is not None:
                return self._dic_memmap[slice_index]["array_spectra"][0, lb:hb]

            # Second most likely case : full slice
            elif lb is None and hb is None:
                return self.get_array_mz(slice_index)

            # Most likely the remaining cases won't be used
            elif lb is None:
                return self._dic_memmap[slice_index]["array_spectra"][0, :hb]

            else:
                return self._dic_memmap[slice_index]["array_spectra"][0, lb:]

        # Else, it returns the required index
        else:
            if lb is not None or hb is not None:
                logging.warning(
                    "Both one or several boundaries and one index have been specified when calling array_spectra. "
                    + "Only the index request will be satisfied."
                )
            return self._dic_memmap[slice_index]["array_spectra"][0, index]

    def get_partial_array_intensity(self, slice_index, lb=None, hb=None, index=None):

        # If not specific index has been provided, it returns a range
        if index is None:

            # Start with most likely case
            if hb is not None and lb is not None:
                return self._dic_memmap[slice_index]["array_spectra"][1, lb:hb]

            # Second most likely case : full slice
            elif lb is None and hb is None:
                return self.get_array_intensity(slice_index)

            # Most likely the remaining cases won't be used
            elif lb is None:
                return self._dic_memmap[slice_index]["array_spectra"][1, :hb]

            else:
                return self._dic_memmap[slice_index]["array_spectra"][1, lb:]

        # Else, it returns the required index
        else:
            if lb is not None or hb is not None:
                logging.warning(
                    "Both one or several boundaries and one index have been specified when calling array_spectra. "
                    + "Only the index request will be satisfied."
                )
            return self._dic_memmap[slice_index]["array_spectra"][1, index]

    def get_partial_array_avg_spectrum(self, slice_index, lb=None, hb=None):

        # Start with most likely case
        if hb is not None and lb is not None:
            return self._dic_memmap[slice_index]["array_avg_spectrum"][:, lb:hb]

        # Second most likely case : full slice
        elif lb is None and hb is None:
            return self.get_array_avg_spectrum(slice_index)

        # Most likely the remaining cases won't be used
        elif lb is None:
            return self._dic_memmap[slice_index]["array_avg_spectrum"][:, :hb]
        else:
            return self._dic_memmap[slice_index]["array_avg_spectrum"][:, lb:]

    def get_lookup_mz(self, slice_index, index):
        # Just return the (one) required lookup to go faster
        return self._dic_memmap[slice_index]["array_lookup_mz"][index]

    def get_cumulated_lookup_mz_image(self, slice_index, index):
        # Just return the (one) required lookup to go faster
        return self._dic_memmap[slice_index]["array_cumulated_lookup_mz_image"][index]

    # ? For the docstring : this function takes only about 5ms to run on all memmaps, and 1ms on a given slice
    # ! Does the GIL handle this properly? Must try with several users at once
    def clean_memory(self, slice_index=None, array=None):

        # Case no array name has been provided
        if array is None:
            l_array_names = [
                "array_spectra",
                "array_avg_spectrum",
                "array_lookup_mz",
                "array_cumulated_lookup_mz_image",
            ]

            # Clean all memmaps if no slice index have been given
            if slice_index is None:
                for index in range(1, self._n_slices + 1):
                    for array_name in l_array_names:
                        self._dic_memmap[index][array_name] = np.memmap(
                            self._path_data + array_name + "_" + str(index) + ".mmap",
                            dtype="float32" if array_name != "array_lookup_mz" else "int32",
                            mode="r",
                            shape=self._dic_lightweight[index][array_name + "_shape"],
                        )

            # Else clean all memmaps of a given slice index
            else:
                for array_name in l_array_names:
                    self._dic_memmap[slice_index][array_name] = np.memmap(
                        self._path_data + array_name + "_" + str(slice_index) + ".mmap",
                        dtype="float32" if array_name != "array_lookup_mz" else "int32",
                        mode="r",
                        shape=self._dic_lightweight[slice_index][array_name + "_shape"],
                    )
        # Case an array name has been provided
        else:
            # Clean all memmaps corresponding to the current array if no slice_index have been given
            if slice_index is None:
                for index in range(1, self._n_slices + 1):
                    self._dic_memmap[index][array] = np.memmap(
                        self._path_data + array + "_" + str(index) + ".mmap",
                        dtype="float32" if array != "array_lookup_mz" else "int32",
                        mode="r",
                        shape=self._dic_lightweight[index][array + "_shape"],
                    )

            # Else clean the memap of the given slice index
            else:
                self._dic_memmap[slice_index][array] = np.memmap(
                    self._path_data + array + "_" + str(slice_index) + ".mmap",
                    dtype="float32" if array != "array_lookup_mz" else "int32",
                    mode="r",
                    shape=self._dic_lightweight[slice_index][array + "_shape"],
                )

    def compute_l_labels(self):
        l_labels = (
            self._df_annotations["name"]
            + "_"
            + self._df_annotations["structure"]
            + "_"
            + self._df_annotations["cation"]
        ).to_list()
        return l_labels
