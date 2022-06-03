# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This class is used to produce the figures and widgets used in the app, themselves requiring data
from the MALDI imaging, and the Allen Brain Atlas, as well as the mapping between the two."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import numpy as np
import logging
from modules.tools.misc import logmem
import plotly.graph_objects as go
import plotly.express as px
from skimage import io
from scipy.ndimage.interpolation import map_coordinates
import pandas as pd
from modules.tools.external_lib.clustergram import Clustergram


# LBAE imports
from modules.tools.image import convert_image_to_base64
from modules.tools.atlas import project_image, slice_to_atlas_transform
from modules.tools.volume import (
    filter_voxels,
    fill_array_borders,
    fill_array_interpolation,
    fill_array_slices,
    crop_array,
)
from config import dic_colors, l_colors
from modules.tools.spectra import (
    compute_image_using_index_and_image_lookup,
    compute_index_boundaries,
    compute_avg_intensity_per_lipid,
    global_lipid_index_store,
    compute_thread_safe_function,
)


# ==================================================================================================
# --- Class
# ==================================================================================================


class Figures:
    """This class is used to produce the figures and widgets used in the app. It uses the special
    attribute __slots__ for faster access to the attributes.

    Attributes:
        _data (MaldiData): MaldiData object, used to manipulate the raw MALDI data.
        _storage (Storage): Used to access the shelve database.
        _atlas (Atlas): Used to manipulate the objects coming from the Allen Brain Atlas.
        dic_normalization_factors (dict): Dictionnary of normalization factors across slices for
            MAIA.


    Methods (parameters are ignored in the docstring below to save space. Please consult the
        docstring of the corresponding methods for more information):

        __init__(): Initialize the Figures class.
        compute_array_basic_images(): Computes a three-dimensional array representing all slices
            from the maldi_data acquisition (TIC) or the corresponding image from the atlas.
        compute_figure_basic_image(): Computes a figure representing slices from the TIC or the
            corresponding image from the atlas.
        compute_figure_slices_3D(): Computes a figure representing all slices from the maldi data in
            3D.
        get_surface(): Computes a Plotly Surface representing the requested slice in 3D.
        compute_image_per_lipid(): Allows to query the MALDI data to extract an image representing
            the intensity of each lipid in the requested slice.
        compute_normalization_factor_across_slices(): Computes a dictionnary of normalization
            factors across all slices.
        build_lipid_heatmap_from_image(): Converts a numpy array into a base64 string, a go.Image,
            or a Plotly Figure.
        compute_heatmap_per_mz(): Computes a heatmap of the lipid expressed in the requested slice
            whose m/z is between the two provided boundaries.
        compute_heatmap_per_lipid_selection(): Computes a heatmap of the sum of expression of the
            requested lipids in the requested slice.
        compute_rgb_array_per_lipid_selection(): Computes a numpy RGB array of expression of the
            requested lipids in the requested slice.
        compute_rgb_image_per_lipid_selection(): Similar to compute_heatmap_per_lipid_selection, but
            computes a RGB image instead of a heatmap.
        compute_spectrum_low_res(): Returns the full (low-resolution) spectrum of the requested
            slice.
        compute_spectrum_high_res(): Returns the full (high-resolution) spectrum of the requested
            slice between the two provided m/z boundaries.
        return_empty_spectrum(): Returns an empty spectrum.
        return_heatmap_lipid(): Either generate a Plotly Figure containing an empty go.Heatmap,
            or complete the figure passed as argument with a proper layout that matches the theme of
            the app.
        compute_treemaps_figure(): Generates a Plotly Figure containing a treemap of the Allen Brain
            Atlas hierarchy.
        compute_3D_root_volume(): Generate a go.Isosurface of the Allen Brain root structure,
            which will be used to enclose the display of lipid expression of other structures in the
            brain.
        get_array_of_annotations(): Returns the array of annotations from the Allen Brain Atlas,
            subsampled to decrease the size of the output.
        compute_l_array_2D(): Gets the list of expression per slice for all slices for the
            computation of the 3D brain volume.
        compute_array_coordinates_3D(): Computes the list of coordinates and expression values for
            the voxels used in the 3D representation of the brain.
        compute_3D_volume_figure(): Computes a Plotly Figure containing a go.Volume object
            representing the expression of the requested lipids in the selected regions.
        compute_clustergram_figure(): Computes a Plotly Clustergram figure, allowing to cluster and
            compare the expression of all the MAIA-transformed lipids in the dataset in the selected
            regions.
        shelve_arrays_basic_figures(): Shelves in the database all the arrays of basic images
            computed in compute_figure_basic_image(), across all slices and all types of arrays.
        shelve_all_l_array_2D(): Precomputes and shelves all the arrays of lipid expression used in
            a 3D representation of the brain.
        shelve_all_arrays_annotation(): Precomputes and shelves the array of structure annotation
            used in a 3D representation of the brain.
    """

    __slots__ = ["_data", "_atlas", "_storage", "dic_normalization_factors"]

    # ==============================================================================================
    # --- Constructor
    # ==============================================================================================

    def __init__(self, maldi_data, storage, atlas, sample=False):
        """Initialize the Figures class.

        Args:
            maldi_data (MaldiData): MaldiData object, used to manipulate the raw MALDI data.
            storage (Storage): Used to access the shelve database.
            atlas (Atlas): Used to manipulate the objects coming from the Allen Brain Atlas.
            sample (bool, optional): If True, only a fraction of the precomputations are made (for
                debug). Default to False.
        """
        logging.info("Initializing Figures object" + logmem())

        # Attribute to easily access the maldi and allen brain atlas data
        self._data = maldi_data
        self._atlas = atlas

        # attribute to access the shelve database
        self._storage = storage

        # Dic of normalization factors across slices for MAIA normalized lipids
        self.dic_normalization_factors = self._storage.return_shelved_object(
            "figures/lipid_selection",
            "dic_normalization_factors",
            force_update=False,
            compute_function=self.compute_normalization_factor_across_slices,
            cache_flask=None,  # No cache since launched at startup
        )

        # Check that treemaps has been computed already. If not, compute it and store it.
        if not self._storage.check_shelved_object("figures/atlas_page/3D", "treemaps"):
            self._storage.return_shelved_object(
                "figures/atlas_page/3D",
                "treemaps",
                force_update=False,
                compute_function=self.compute_treemaps_figure,
            ),

        # Check that 3D slice figure has been computed already. If not, compute it and store it.
        if not self._storage.check_shelved_object("figures/3D_page", "slices_3D"):
            self._storage.return_shelved_object(
                "figures/3D_page",
                "slices_3D",
                force_update=False,
                compute_function=self.compute_figure_slices_3D,
            )

        # Check that the 3D root volume figure has been computed already. If not, compute it and
        # store it.
        if not self._storage.check_shelved_object("figures/3D_page", "volume_root"):
            self._storage.return_shelved_object(
                "figures/3D_page",
                "volume_root",
                force_update=False,
                compute_function=self.compute_3D_root_volume,
            )

        # Check that all basic figures in the load_slice page are present, if not, compute them
        if not self._storage.check_shelved_object(
            "figures/load_page", "arrays_basic_figures_computed"
        ):
            self.shelve_arrays_basic_figures()

        # Check that the lipid distributions for all slices have been computed, if not, compute them
        if not self._storage.check_shelved_object("figures/3D_page", "arrays_expression_computed"):
            self.shelve_all_l_array_2D(sample=sample)

        # Check that all arrays of annotations have been computed, if not, compute them
        if not self._storage.check_shelved_object("figures/3D_page", "arrays_annotation_computed"):
            self.shelve_all_arrays_annotation()

        logging.info("Figures object instantiated" + logmem())

    # ==============================================================================================
    # --- Methods used mainly in load_slice
    # ==============================================================================================

    def compute_array_basic_images(self, type_figure="warped_data"):
        """This function computes and returns a three-dimensional array representing all slices from
        the maldi_data acquisition (TIC) or the corresponding image from the atlas. No spectral data
        is read in the process, as the arrays corresponding to the images are directly stored as
        tiff files in the dataset.

        Args:
            type_figure (str, optional): To be chosen among "original_data", "warped_data",
                "projection_corrected", "atlas". Depending on the chosen type, the final array will
                correspond to either the original images ("original_data"), the warped and upscaled
                images ("warped_data"), the warped and upscaled images, whose pixels outside of
                annotations regions have been zero-ed out ("projection_corrected"), or the images
                from the Allen Brain atlas projected onto the same plane as the corresponding slice
                from the MALDI data ("atlas"). Default to "warped_data".

        Returns:
            np.ndarray: A three-dimensional array representing all slices from the maldi_data
                acquisition (TIC) or the corresponding image from the atlas. The first dimension
                corresponds to the slices, the second and third to the images themselves.
        """

        # Check for all array types
        if type_figure == "original_data":
            array_images = self._data.compute_padded_original_images()

        elif type_figure == "warped_data":
            if self._data._sample_data:
                with np.load("data_sample/tiff_files/warped_data.npz") as handle:
                    array_images = handle["array_warped_data"]
            else:
                array_images = io.imread("data/tiff_files/warped_data.tif")
        elif type_figure == "projection_corrected":
            array_images = self._atlas.array_projection_corrected
        elif type_figure == "atlas":
            (
                array_projected_images_atlas,
                array_projected_simplified_id,
            ) = self._storage.return_shelved_object(
                "atlas/atlas_objects",
                "array_images_atlas",
                force_update=False,
                compute_function=self._atlas.prepare_and_compute_array_images_atlas,
                zero_out_of_annotation=True,
            )
            array_images = array_projected_images_atlas
        else:
            logging.warning('The type of requested array "{}" does not exist.'.format(type_figure))
            return None

        # If the array is not uint8, convert it to gain space
        if array_images.dtype != np.uint8:
            array_images = np.array(array_images, dtype=np.uint8)
        return array_images

    def compute_figure_basic_image(
        self, type_figure, index_image, plot_atlas_contours=True, only_contours=False, draw=False
    ):
        """This function computes and returns a figure representing slices from the maldi_data
        acquisition (TIC) or the corresponding image from the atlas. The data is read directly from
        the array computed in self.compute_array_basic_images().

        Args:
            type_figure (str): To be chosen among "original_data", "warped_data",
                "projection_corrected", "atlas". Depending on the chosen type, the final figure will
                correspond to either the original images ("original_data"), the warped and upscaled
                images ("warped_data"), the warped and upscaled images, whose pixels outside of
                annotations regions have been zero-ed out ("projection_corrected"), or the images
                from the Allen Brain atlas projected onto the same plane as the corresponding slice
                from the MALDI data ("atlas").
            index_image (int): Index of the requested slice image.
            plot_atlas_contours (bool, optional): If True, the atlas contours annotation is
                superimposed with the slice image. Defaults to True.
            only_contours (bool, optional): If True, only output the atlas contours annotation. All
                the other arugments but plot_atlas_contours (which must be True) get ignored.
                Defaults to False.
            draw (bool, optional): If True, the figure can be drawed on (used for region selection,
                in page region_analysis). Defaults to False.

        Returns:
            go.Figure: A Plotly figure representing the requested slice image of the requested type.
        """

        # If only boundaries is requested, force the computation of atlas contours
        if only_contours:
            plot_atlas_contours = True

        else:
            # Get array of images
            array_images = self._storage.return_shelved_object(
                "figures/load_page",
                "array_basic_images",
                force_update=False,
                compute_function=self.compute_array_basic_images,
                type_figure=type_figure,
            )

            # Get image at specified index
            array_image = array_images[index_image]

        # Add the contours if requested
        if plot_atlas_contours:
            array_image_atlas = self._atlas.list_projected_atlas_borders_arrays[index_image]
        else:
            array_image_atlas = None

        # Create figure
        fig = go.Figure()

        # Compute image from our data if not only the atlas annotations are requested
        if not only_contours:
            fig.add_trace(
                go.Image(
                    visible=True,
                    source=convert_image_to_base64(
                        array_image, overlay=array_image_atlas, transparent_zeros=True
                    ),
                    hoverinfo="none",
                )
            )

            # Add the labels only if it's not a simple annotation illustration
            fig.update_xaxes(
                title_text=self._atlas.bg_atlas.space.axis_labels[0][1], title_standoff=0
            )

        else:
            fig.add_trace(
                go.Image(
                    visible=True,
                    source=convert_image_to_base64(
                        array_image_atlas,
                        optimize=True,
                        binary=True,
                        type="RGBA",
                        decrease_resolution_factor=8,
                    ),
                    hoverinfo="none",
                )
            )

        # Improve layout
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)
        fig.update_layout(
            margin=dict(t=0, r=0, b=0, l=0),
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False),
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        if draw:
            fig.update_layout(
                dragmode="drawclosedpath",
                newshape=dict(
                    fillcolor=l_colors[0], opacity=0.7, line=dict(color="white", width=1)
                ),
                autosize=True,
            )

        return fig

    def compute_figure_slices_3D(self, reduce_resolution_factor=20):
        """This function computes and returns a figure representing the slices from the maldi data
        in 3D.

        Args:
            reduce_resolution_factor (int, optional): Divides (reduce) the initial resolution of the
                data. Needed as the resulting figure can be very heavy. Defaults to 20.

        Returns:
            go.Figure: A Plotly figure representing the slices from the MALDI acquisitions in 3D.
        """
        # Get transform parameters (a,u,v) for each slice
        l_transform_parameters = self._storage.return_shelved_object(
            "atlas/atlas_objects",
            "l_transform_parameters",
            force_update=False,
            compute_function=self._atlas.compute_projection_parameters,
        )

        # Reduce resolution of the slices
        new_dims = []
        n_slices = self._atlas.array_coordinates_warped_data.shape[0]
        d1 = self._atlas.array_coordinates_warped_data.shape[1]
        d2 = self._atlas.array_coordinates_warped_data.shape[2]
        for original_length, new_length in zip(
            self._atlas.array_projection_corrected.shape,
            (
                n_slices,
                int(round(d1 / reduce_resolution_factor)),
                int(round(d2 / reduce_resolution_factor)),
            ),
        ):
            new_dims.append(np.linspace(0, original_length - 1, new_length))

        coords = np.meshgrid(*new_dims, indexing="ij")
        array_projection_small = map_coordinates(self._atlas.array_projection_corrected, coords)

        # Build Figure, with several frames as it will be slidable
        fig = go.Figure(
            frames=[
                go.Frame(
                    data=self.get_surface(
                        i, l_transform_parameters, array_projection_small, reduce_resolution_factor
                    ),
                    name=str(i + 1),
                )
                if i != 12 and i != 8
                else go.Frame(
                    data=self.get_surface(
                        i - 1,
                        l_transform_parameters,
                        array_projection_small,
                        reduce_resolution_factor,
                    ),
                    name=str(i + 1),
                )
                for i in range(0, self._data.get_slice_number(), 1)
            ]
        )
        fig.add_trace(
            self.get_surface(
                0, l_transform_parameters, array_projection_small, reduce_resolution_factor
            )
        )

        # Add a slider
        def frame_args(duration):
            return {
                "frame": {"duration": duration},
                "mode": "immediate",
                "fromcurrent": True,
                "transition": {"duration": duration, "easing": "linear"},
            }

        sliders = [
            {
                "pad": {"b": 5, "t": 10},
                "len": 0.9,
                "x": 0.05,
                "y": 0,
                "steps": [
                    {
                        "args": [[f.name], frame_args(0)],
                        "label": str(k),
                        "method": "animate",
                    }
                    for k, f in enumerate(fig.frames)
                ],
                "currentvalue": {
                    "visible": False,
                },
            }
        ]

        # Layout
        fig.update_layout(
            scene=dict(
                aspectratio=dict(x=1.5, y=1, z=1),
                yaxis=dict(
                    range=[0.0, 0.35],
                    autorange=False,
                    backgroundcolor="rgba(0,0,0,0)",
                    color="grey",
                    gridcolor="grey",
                ),
                zaxis=dict(
                    range=[0.2, -0.02],
                    autorange=False,
                    backgroundcolor="rgba(0,0,0,0)",
                    color="grey",
                    gridcolor="grey",
                ),
                xaxis=dict(
                    range=[0.0, 0.35],
                    autorange=False,
                    backgroundcolor="rgba(0,0,0,0)",
                    color="grey",
                    gridcolor="grey",
                ),
            ),
            margin=dict(t=0, r=0, b=0, l=0),
            template="plotly_dark",
            sliders=sliders,
        )

        # No display of tick labels as they're wrong anyway
        fig.update_layout(
            scene=dict(
                xaxis=dict(showticklabels=False),
                yaxis=dict(showticklabels=False),
                zaxis=dict(showticklabels=False),
            ),
            paper_bgcolor="rgba(0,0,0,0.)",
            plot_bgcolor="rgba(0,0,0,0.)",
        )
        return fig

    # Part of this function could probably be compiled with numba with some effort, but there's no
    # need as it's precomupted in a reasonable time anyway.
    def get_surface(
        self, slice_index, l_transform_parameters, array_projection, reduce_resolution_factor
    ):
        """This function returns a Plotly Surface representing the requested slice in 3D.

        Args:
            slice_index (int): Index of the requested slice.
            l_transform_parameters (list(np.ndarray)): A list of tuples containing the parameters
                for the transformation of the slice coordinates from 2D to 3D and conversely.
            array_projection (np.ndarray): The coordinates of the requested slice in 2D.
            reduce_resolution_factor (int, optional): Divides (reduce) the initial resolution of the
                data. Needed as the resulting figure can be very heavy. Defaults to 20.
        Returns:
            go.Surface: A Plotly Surface representing the requested slice in 3D.
        """

        #  Get the parameters for the transformation of the coordinats from 2D to 3D
        a, u, v = l_transform_parameters[slice_index]

        # Build 3 empty lists, which will contain the 3D coordinates of the requested slice
        ll_x = []
        ll_y = []
        ll_z = []

        # Loop over the first 2D coordinate of the slice
        for i, lambd in enumerate(range(array_projection[slice_index].shape[0])):
            l_x = []
            l_y = []
            l_z = []

            # Loop over the second 2D coordinate of the slice
            for j, mu in enumerate(range(array_projection[slice_index].shape[1])):

                # Get rescaled 3D coordinates
                x_atlas, y_atlas, z_atlas = (
                    np.array(
                        slice_to_atlas_transform(
                            a, u, v, lambd * reduce_resolution_factor, mu * reduce_resolution_factor
                        )
                    )
                    * self._atlas.resolution
                    / 1000
                )
                l_x.append(z_atlas)
                l_y.append(x_atlas)
                l_z.append(y_atlas)

            # In case the 3D coordinate was not acquired, skip the current coordinate
            if l_x != []:
                ll_x.append(l_x)
                ll_y.append(l_y)
                ll_z.append(l_z)

        # Build a 3D surface from the 3D coordinates for the current slice
        surface = go.Surface(
            z=np.array(ll_z),
            x=np.array(ll_x),
            y=np.array(ll_y),
            surfacecolor=array_projection[slice_index].astype(np.int32),
            cmin=0,
            cmax=255,
            colorscale="viridis",
            opacityscale=[[0, 0], [0.1, 1], [1, 1]],
            showscale=False,
        )
        return surface

    # ==============================================================================================
    # --- Methods used mainly in lipid_selection
    # ==============================================================================================

    def compute_image_per_lipid(
        self,
        slice_index,
        lb_mz,
        hb_mz,
        RGB_format=True,
        normalize=True,
        log=False,
        projected_image=True,
        apply_transform=False,
        lipid_name="",
        cache_flask=None,
    ):
        """This function allows to query the MALDI data to extract an image in the form of a Numpy
        array representing the intensity of the lipid peaking between the values lb_mz and hb_mz in
        the spectral data, for the slice slice_index.

        Args:
            slice_index (int): Index of the requested slice.
            lb_mz (float): Lower boundary for the spectral data to query.
            hb_mz (float): Higher boundary for the spectral data to query.
            RGB_format (bool, optional): If True, the values in the array are between 0 and 255,
                given that the data has been normalized beforehand. Else, between 0 and 1. This
                parameter only makes sense if the data has been normalized beforehand. Defaults to
                True.
            normalize (bool, optional): If True, and the lipid has been MAIA transformed (and is
                provided with the parameter lipid_name) and apply_transform is True, the resulting
                array is normalized according to a factor computed across all slice. If MAIA has not
                been applied to the current selection or apply_transform is False, it is normalized
                according to the 99th percentile. Else, it is not normalized. Defaults to True.
            log (bool, optional): If True, the resulting array is log-transformed. This is useful in
                case of low expression. Defaults to False.
            projected_image (bool, optional): If True, the pixels of the original acquisition get
                matched to a higher-resolution, warped space. The gaps are filled by duplicating the
                most appropriate pixels (see dosctring of Atlas.project_image() for more
                information). Defaults to True.
            apply_transform (bool, optional): If True, applies the MAIA transform (if possible) to
                the current selection, given that the parameter normalize is also True, and that
                lipid_name corresponds to an existing lipid. Defaults to False.
            lipid_name (str, optional): Name of the lipid that must be MAIA-transformed, if
                apply_transform and normalize are True. Defaults to "".
            cache_flask (flask_caching.Cache, optional): Cache of the Flask database. If set to
                None, the reading of memory-mapped data will not be multithreads-safe. Defaults to
                None.
        Returns:
            np.ndarray: An image (in the form of a numpy array) representing the intensity of the
                lipid peaking between the values lb_mz and hb_mz in the spectral data, for the slice
                slice_index.
        """
        logging.info("Entering compute_image_per_lipid")

        # Get image from raw mass spec data
        image = compute_thread_safe_function(
            compute_image_using_index_and_image_lookup,
            cache_flask,
            self._data,
            slice_index,
            lb_mz,
            hb_mz,
            self._data.get_array_spectra(slice_index),
            self._data.get_array_lookup_pixels(slice_index),
            self._data.get_image_shape(slice_index),
            self._data.get_array_lookup_mz(slice_index),
            self._data.get_array_cumulated_lookup_mz_image(slice_index),
            self._data.get_divider_lookup(slice_index),
            self._data.get_array_peaks_transformed_lipids(slice_index),
            self._data.get_array_corrective_factors(slice_index).astype(np.float32),
            apply_transform=apply_transform,
        )
        # Log-transform the image if requested
        if log:
            image = np.log(image + 1)

        # Normalize the image if requested
        if normalize:

            # Normalize across slice if the lipid has been MAIA transformed
            if lipid_name in self.dic_normalization_factors and apply_transform:

                perc = self.dic_normalization_factors[lipid_name]
                logging.info("Normalization made with to percentile computed across all slices.")
            else:
                # Normalize by 99 percentile
                perc = np.percentile(image, 99.0)
            if perc == 0:
                perc = np.max(image)
            if perc == 0:
                perc = 1
            image = image / perc
            image = np.clip(0, 1, image)

        # Turn to RGB format if requested
        if RGB_format:
            image *= 255

        # Change dtype if normalized and RGB to save space
        if normalize and RGB_format:
            image = np.round(image).astype(np.uint8)

        # Project image into cleaned and higher resolution version
        if projected_image:
            image = project_image(
                slice_index, image, self._atlas.array_projection_correspondence_corrected
            )
        return image

    def compute_normalization_factor_across_slices(self, cache_flask=None):
        """This function computes a dictionnary of normalization factors (used for MAIA-transformed
        lipids) across all slices (99th percentile of expression).

        Args:
            cache_flask (flask_caching.Cache, optional): Cache of the Flask database. If set to
                None, the reading of memory-mapped data will not be multithreads-safe. Defaults to
                None.
        Returns:
            dict: A dictionnary associating, for each MAIA-transformed lipid name, the 99th
                percentile of the intensity across all slices.
        """
        logging.info(
            "Compute normalization factor across slices for MAIA transformed lipids..."
            + " It may takes a while"
        )
        dic_max_percentile = {}
        # Simulate a click on all MAIA transformed lipids
        for (
            index,
            (name, structure, cation, mz),
        ) in self._data.get_annotations_MAIA_transformed_lipids().iterrows():
            max_perc = 0
            for slice_index in range(1, self._data.get_slice_number() + 1):

                # Find lipid location
                l_lipid_loc = (
                    self._data.get_annotations()
                    .index[
                        (self._data.get_annotations()["name"] == name)
                        & (self._data.get_annotations()["structure"] == structure)
                        & (self._data.get_annotations()["slice"] == slice_index)
                        & (self._data.get_annotations()["cation"] == cation)
                    ]
                    .tolist()
                )

                # If several lipids correspond to the selection, we have a problem...
                if len(l_lipid_loc) >= 1:
                    index = l_lipid_loc[-1]

                    # get final lipid name
                    lipid_string = name + "_" + structure + "_" + cation

                    # get lipid bounds
                    lb_mz = float(self._data.get_annotations().iloc[index]["min"])
                    hb_mz = float(self._data.get_annotations().iloc[index]["max"])

                    # Get corresponding image
                    image = compute_thread_safe_function(
                        compute_image_using_index_and_image_lookup,
                        cache_flask,
                        self._data,
                        slice_index,
                        lb_mz,
                        hb_mz,
                        self._data.get_array_spectra(slice_index),
                        self._data.get_array_lookup_pixels(slice_index),
                        self._data.get_image_shape(slice_index),
                        self._data.get_array_lookup_mz(slice_index),
                        self._data.get_array_cumulated_lookup_mz_image(slice_index),
                        self._data.get_divider_lookup(slice_index),
                        self._data.get_array_peaks_transformed_lipids(slice_index),
                        self._data.get_array_corrective_factors(slice_index).astype(np.float32),
                        apply_transform=False,
                    )

                    # Check 99th percentile for normalization
                    perc = np.percentile(image, 99.0)

                    # perc must be quite small in theory... otherwise it's a bug
                    if perc > max_perc:  # and perc<1:
                        max_perc = perc

            # Store max percentile across slices
            dic_max_percentile[lipid_string] = max_perc

        return dic_max_percentile

    def build_lipid_heatmap_from_image(
        self,
        image,
        return_base64_string=False,
        draw=False,
        type_image=None,
        return_go_image=False,
    ):
        """This function converts a numpy array into a base64 string, which can be returned
        directly, or itself be turned into a go.Image, which can be returned directly, or be
        turned into a Plotly Figure, which will be returned.

        Args:
            image (np.ndarray): A numpy array representing the image to be converted. Possibly with
                several channels.
            return_base64_string (bool, optional): If True, the base64 string of the image is
                returned directly, before any figure building. Defaults to False.
            draw (bool, optional): If True, the user will have the possibility to draw on the
                resulting Plotly Figure. Defaults to False.
            type_image (string, optional): The type of the image to be converted to a base64 string.
                If image_array is in 3D, type must be RGB. If 4D, type must be RGBA. Else, no
                requirement (None). Defaults to None.
            return_go_image (bool, optional): If True, the go.Image is returned directly, before
                being integrated to a Plotly Figure. Defaults to False.

        Returns:
            Depending on the inputted arguments, may either return a base64 string, a go.Image, or
            a Plotly Figure.
        """

        logging.info("Converting image to string")

        # Set optimize to False to gain computation time
        base64_string = convert_image_to_base64(
            image, type=type_image, overlay=None, transparent_zeros=True, optimize=False
        )

        # Either return image directly
        if return_base64_string:
            return base64_string

        # Or compute heatmap as go image if needed
        logging.info("Converting image to go image")
        final_image = go.Image(
            visible=True,
            source=base64_string,
        )

        # Potentially return the go image directly
        if return_go_image:
            return final_image

        # Or build ploty graph
        fig = go.Figure(final_image)

        # Improve graph layout
        fig.update_layout(
            margin=dict(t=0, r=0, b=0, l=0),
            newshape=dict(
                fillcolor=dic_colors["blue"], opacity=0.7, line=dict(color="white", width=1)
            ),
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False),
            # Do not specify height for now as plotly is buggued and resets if switching pages
            # height=500,
        )
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)
        fig.update(layout_coloraxis_showscale=False)

        # Set how the image should be annotated
        if draw:
            fig.update_layout(dragmode="drawclosedpath")

        # Set background color to zero
        fig.layout.template = "plotly_dark"
        fig.layout.plot_bgcolor = "rgba(0,0,0,0)"
        fig.layout.paper_bgcolor = "rgba(0,0,0,0)"
        logging.info("Returning figure")

        return fig

    def compute_heatmap_per_mz(
        self,
        slice_index,
        lb_mz=None,
        hb_mz=None,
        draw=False,
        projected_image=True,
        return_base64_string=False,
        cache_flask=None,
    ):
        """This function takes two boundaries and a slice index, and returns a heatmap of the lipid
        expressed in the slice whose m/z is between the two boundaries.

        Args:
            slice_index (int): The index of the requested slice.
            lb_mz (float, optional): The lower m/z boundary. Defaults to None.
            hb_mz (float, optional): The higher m/z boundary. Defaults to None.
            draw (bool, optional): If True, the user will have the possibility to draw on the
                resulting Plotly Figure. Defaults to False.
            projected_image (bool, optional): If True, the pixels of the original acquisition get
                matched to a higher-resolution, warped space. The gaps are filled by duplicating the
                most appropriate pixels (see dosctring of Atlas.project_image() for more
                information). Defaults to True.
            return_base64_string (bool, optional): If True, the base64 string of the image is
                returned directly, before any figure building. Defaults to False.
            cache_flask (flask_caching.Cache, optional): Cache of the Flask database. If set to
                None, the reading of memory-mapped data will not be multithreads-safe. Defaults to
                None.
        Returns:
            Depending on the value return_base64_string, may either return a base64 string, or
            a Plotly Figure.
        """

        logging.info("Starting figure computation, from mz boundaries")

        # Upper bound lower than the lowest m/z value and higher that the highest m/z value
        if lb_mz is None:
            lb_mz = 200
        if hb_mz is None:
            hb_mz = 1800

        logging.info("Getting image array")

        # Compute image with given bounds
        image = self.compute_image_per_lipid(
            slice_index,
            lb_mz,
            hb_mz,
            RGB_format=True,
            projected_image=projected_image,
            cache_flask=cache_flask,
        )

        # Compute corresponding figure
        fig = self.build_lipid_heatmap_from_image(
            image, return_base64_string=return_base64_string, draw=draw
        )

        return fig

    def compute_heatmap_per_lipid_selection(
        self,
        slice_index,
        ll_t_bounds,
        normalize=True,
        projected_image=True,
        apply_transform=False,
        ll_lipid_names=None,
        return_base64_string=False,
        cache_flask=None,
    ):
        """This function is very similar to compute_heatmap_per_mz, but it takes a list of lipid
        boundaries, possibly along with lipid names, instead of just two boundaries. It returns a
        heatmap of the sum of expression of the requested lipids in the slice.

        Args:
            slice_index (int): The index of the requested slice.
            ll_t_bounds (list(list(tuple))): A list of lists of lipid boundaries (tuples). The first
                list is used to separate image channels (although this is not used in the function).
                The second list is used to separate lipid.
            normalize (bool, optional): If True, and the lipid has been MAIA transformed (and is
                provided with the parameter lipid_name) and apply_transform is True, the resulting
                array is normalized according to a factor computed across all slice. If MAIA has not
                been applied to the current selection or apply_transform is False, it is normalized
                according to the 99th percentile. Else, it is not normalized. Defaults to True.
            projected_image (bool, optional): If True, the pixels of the original acquisition get
                matched to a higher-resolution, warped space. The gaps are filled by duplicating the
                most appropriate pixels (see dosctring of Atlas.project_image() for more
                information). Defaults to True.
            apply_transform (bool, optional): If True, applies the MAIA transform (if possible) to
                the current selection, given that the parameter normalize is also True, and that
                lipid_name corresponds to an existing lipid. Defaults to False.
            ll_lipid_names (list(list(int)), optional): List of list of lipid names that must be
                MAIA-transformed, if apply_transform and normalize are True. The first list is used
                to separate channels, when applicable. Defaults to None.
            return_base64_string (bool, optional): If True, the base64 string of the image is
                returned directly, before any figure building. Defaults to False.
            cache_flask (flask_caching.Cache, optional): Cache of the Flask database. If set to
                None, the reading of memory-mapped data will not be multithreads-safe. Defaults to
                None.

        Returns:
            Depending on the value return_base64_string, may either return a base64 string, or
            a Plotly Figure.
        """

        logging.info("Compute heatmap per lipid selection" + str(ll_t_bounds))

        # Start from empty image and add selected lipids
        # * Caution: array must be int, float gets badly converted afterwards
        image = np.zeros(self._atlas.image_shape, dtype=np.int32)

        # Build empty lipid names if not provided
        if ll_lipid_names is None:
            ll_lipid_names = [["" for y in l_t_bounds] for l_t_bounds in ll_t_bounds]

        # Loop over channels
        for l_t_bounds, l_lipid_names in zip(ll_t_bounds, ll_lipid_names):
            if l_t_bounds is not None:

                # Loop over lipids
                for boundaries, lipid_name in zip(l_t_bounds, l_lipid_names):
                    if boundaries is not None:
                        (lb_mz, hb_mz) = boundaries

                        # Cmpute expression image per lipid
                        image_temp = self.compute_image_per_lipid(
                            slice_index,
                            lb_mz,
                            hb_mz,
                            RGB_format=True,
                            normalize=normalize,
                            projected_image=projected_image,
                            apply_transform=apply_transform,
                            lipid_name=lipid_name,
                            cache_flask=cache_flask,
                        )
                        image += image_temp

        # Compute corresponding figure
        fig = self.build_lipid_heatmap_from_image(image, return_base64_string=return_base64_string)

        return fig

    def compute_rgb_array_per_lipid_selection(
        self,
        slice_index,
        ll_t_bounds,
        normalize_independently=True,
        projected_image=True,
        log=False,
        apply_transform=False,
        ll_lipid_names=None,
        cache_flask=None,
    ):
        """This function computes a numpy RGB array (each pixel has 3 intensity values) of
        expression of the requested lipids (those whose m/z values are in ll_t_bounds) in the slice.

        Args:
            slice_index (int): The index of the requested slice.
            ll_t_bounds (list(list(tuple))): A list of lists of lipid boundaries (tuples). The first
                list is used to separate image channels. The second list is used to separate lipid.
            normalize_independently (bool, optional): If True, each lipid intensity array is
                normalized independently, regardless of other lipids or channel used. Defaults to
                True.
            projected_image (bool, optional): If True, the pixels of the original acquisition get
                matched to a higher-resolution, warped space. The gaps are filled by duplicating the
                most appropriate pixels (see dosctring of Atlas.project_image() for more
                information). Defaults to True.
            log (bool, optional): If True, the resulting array corresponds to log-transformed
                expression, for each lipid. Defaults to False.
            apply_transform (bool, optional): If True, applies the MAIA transform (if possible) to
                the current selection, given that the parameter normalize is also True, and that
                lipid_name corresponds to an existing lipid. Defaults to False.
            ll_lipid_names (list(list(int)), optional): List of list of lipid names that must be
                MAIA-transformed, if apply_transform and normalize are True. The first list is used
                to separate channels, when applicable. Defaults to None.
            cache_flask (flask_caching.Cache, optional): Cache of the Flask database. If set to
                None, the reading of memory-mapped data will not be multithreads-safe. Defaults to
                None.

        Returns:
            np.ndarray: A three-dimensional RGB numpy array (of uint8 dtype). The first two
            dimensions correspond to the acquisition image shape, and the third dimension
            corresponds to the channels.
        """

        # Empty lipid names if no names provided
        if ll_lipid_names is None:
            ll_lipid_names = [
                ["" for y in l_t_bounds] if l_t_bounds is not None else [""]
                for l_t_bounds in ll_t_bounds
            ]

        # Build a list of empty images and add selected lipids for each channel
        l_images = []

        # Loop over channels
        for l_boundaries, l_names in zip(ll_t_bounds, ll_lipid_names):
            image = np.zeros(
                self._atlas.image_shape
                if projected_image
                else self._data.get_image_shape(slice_index)
            )
            if l_boundaries is not None:

                # Loop over lipids
                for boundaries, lipid_name in zip(l_boundaries, l_names):
                    if boundaries is not None:
                        (lb_mz, hb_mz) = boundaries

                        # Cmpute expression image per lipid
                        image_temp = self.compute_image_per_lipid(
                            slice_index,
                            lb_mz,
                            hb_mz,
                            RGB_format=True,
                            normalize=normalize_independently,
                            projected_image=projected_image,
                            log=log,
                            apply_transform=apply_transform,
                            lipid_name=lipid_name,
                            cache_flask=cache_flask,
                        )

                        image += image_temp

            l_images.append(image)

        # Reoder axis to match plotly go.image requirements
        array_image = np.moveaxis(np.array(l_images), 0, 2)

        return np.asarray(array_image, dtype=np.uint8)

    def compute_rgb_image_per_lipid_selection(
        self,
        slice_index,
        ll_t_bounds,
        normalize_independently=True,
        projected_image=True,
        log=False,
        return_image=False,
        apply_transform=False,
        ll_lipid_names=None,
        return_base64_string=False,
        cache_flask=None,
    ):
        """This function is very similar to compute_heatmap_per_lipid_selection, but it returns a
        RGB image instead of a heatmap.

        Args:
            slice_index (int): The index of the requested slice.
            ll_t_bounds (list(list(tuple))): A list of lists of lipid boundaries (tuples). The first
                list is used to separate image channels. The second list is used to separate lipid.
            normalize_independently (bool, optional): If True, each lipid intensity array is
                normalized independently, regardless of other lipids or channel used. Defaults to
                True.
            projected_image (bool, optional): If True, the pixels of the original acquisition get
                matched to a higher-resolution, warped space. The gaps are filled by duplicating the
                most appropriate pixels (see dosctring of Atlas.project_image() for more
                information). Defaults to True.
            log (bool, optional): If True, the resulting array corresponds to log-transformed
                expression, for each lipid. Defaults to False.
            return_image (bool, optional): If True, a go.Image is returned directly, instead of a
                Plotly Figure. Defaults to False.
            apply_transform (bool, optional): If True, applies the MAIA transform (if possible) to
                the current selection, given that the parameter normalize is also True, and that
                lipid_name corresponds to an existing lipid. Defaults to False.
            ll_lipid_names (list(list(int)), optional): List of list of lipid names that must be
                MAIA-transformed, if apply_transform and normalize are True. The first list is used
                to separate channels, when applicable. Defaults to None.
            return_base64_string (bool, optional): If True, the base64 string of the image is
                returned directly, before any figure building. Defaults to False.
            cache_flask (flask_caching.Cache, optional): Cache of the Flask database. If set to
                None, the reading of memory-mapped data will not be multithreads-safe. Defaults to
                None.

        Returns:
            Depending on the inputted arguments, may either return a base64 string, a go.Image, or
            a Plotly Figure.
        """

        logging.info("Started RGB image computation for slice " + str(slice_index) + logmem())

        # Empty lipid names if no names provided
        if ll_lipid_names is None:
            ll_lipid_names = [["" for y in l_t_bounds] for l_t_bounds in ll_t_bounds]

        logging.info("Acquiring array_image for slice " + str(slice_index) + logmem())

        # Get RGB array for the current lipid selection
        array_image = self.compute_rgb_array_per_lipid_selection(
            slice_index,
            ll_t_bounds,
            normalize_independently=normalize_independently,
            projected_image=projected_image,
            log=log,
            apply_transform=apply_transform,
            ll_lipid_names=ll_lipid_names,
            cache_flask=cache_flask,
        )

        logging.info("Returning fig for slice " + str(slice_index) + logmem())

        # Build the correspondig figure
        return self.build_lipid_heatmap_from_image(
            array_image,
            return_base64_string=return_base64_string,
            draw=False,
            type_image="RGB",
            return_go_image=return_image,
        )

    def compute_spectrum_low_res(self, slice_index, annotations=None):
        """This function returns the full (low-resolution) spectrum of the requested slice.

        Args:
            slice_index (int): The slice index of the requested slice.
            annotations (list(tuple), optional): A list of m/z boundaries (one for each lipid to
                annotate), corresponding to the position of colored box superimposed on the spectra.
                Defaults to None.
        Returns:
            go.Figure: A Plotly Figure representing the low-resolution spectrum.
        """

        # Define figure data
        data = go.Scattergl(
            x=self._data.get_array_avg_spectrum_downsampled(slice_index)[0, :],
            y=self._data.get_array_avg_spectrum_downsampled(slice_index)[1, :],
            visible=True,
            line_color=dic_colors["blue"],
            fill="tozeroy",
        )
        # Define figure layout
        layout = go.Layout(
            margin=dict(t=50, r=0, b=10, l=0),
            showlegend=False,
            xaxis=dict(rangeslider={"visible": False}, title="m/z"),
            yaxis=dict(fixedrange=False, title="Intensity"),
            template="plotly_dark",
            autosize=True,
            title={
                "text": "Low resolution spectrum (averaged across pixels)",
                "y": 0.92,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
                "font": dict(
                    size=14,
                ),
            },
            paper_bgcolor="rgba(0,0,0,0.3)",
            plot_bgcolor="rgba(0,0,0,0.3)",
        )

        # Build figure
        fig = go.Figure(data=data, layout=layout)

        # Annotate selected lipids with vertical bars
        if annotations is not None:
            for color, annot in zip(["red", "green", "blue"], annotations):
                if annot is not None:
                    fig.add_vrect(
                        x0=annot[0],
                        x1=annot[1],
                        fillcolor=dic_colors[color],
                        opacity=0.4,
                        line_color=dic_colors[color],
                    )
        return fig

    def compute_spectrum_high_res(
        self,
        slice_index,
        lb=None,
        hb=None,
        annotations=None,
        force_xlim=False,
        plot=True,
        standardization=False,
        cache_flask=None,
    ):
        """This function returns the high-resolution spectrum of the requested slice between the two
        provided m/z boundaries lb and hb. If boundaries are not provided, it returns an empty
        spectrum.

        Args:
            slice_index (int): The slice index of the requested slice.
            lb (float, optional): The lower m/z boundary below which the spectrum to display must
                be cropped. Defaults to None.
            hb (float, optional): The higher m/z boundary below which the spectrum to display must
                be cropped. Defaults to None.
            annotations (list(tuple), optional): A list of m/z boundaries (one for each lipid to
                annotate), corresponding to the position of colored box superimposed on the spectra.
                Defaults to None.
            force_xlim (bool, optional): If Truen the zoom level will be set to enclose lb and hb,
                although that may not be the tightest region to enclose the data. Defaults to False.
            plot (bool, optional): If False, only the plotting data (m/z and intensities arrays)
                will be returned. Defaults to True.
            standardization (bool, optional): If True, the displayed spectrum is standardized with
                MAIA when possible.
            cache_flask (flask_caching.Cache, optional): Cache of the Flask database. If set to
                None, the reading of memory-mapped data will not be multithreads-safe. Defaults to
                None.
        Returns:
            Depending on the value of the boundaries, and the plot parameter, it may return a Plotly
            Figure containing an empty spectrum, or a spectrum between the two provided boundaries,
            or the corresponding data of such a spectrum.
        """

        # Define default values for graph (empty)
        if lb is None and hb is None:
            x = ([],)
            y = ([],)

        # If boundaries are provided, get their index
        else:
            index_lb, index_hb = compute_thread_safe_function(
                compute_index_boundaries,
                cache_flask,
                self._data,
                slice_index,
                lb,
                hb,
                array_spectra_avg=self._data.get_array_avg_spectrum(
                    slice_index, standardization=standardization
                ),
                lookup_table=self._data.get_array_lookup_mz_avg(slice_index),
            )

            def return_x_y(array):
                x = np.copy(array[0, index_lb:index_hb])
                y = np.copy(array[1, index_lb:index_hb])
                return x, y

            # Get x, y in a thread safe fashion
            # No need to clean memory as it's really small
            x, y = compute_thread_safe_function(
                return_x_y,
                cache_flask,
                self._data,
                slice_index,
                self._data.get_array_avg_spectrum(slice_index, standardization=standardization),
            )

        # In case download without plotting
        if not plot:
            return x, y

        # Define figure data
        data = go.Scattergl(x=x, y=y, visible=True, line_color=dic_colors["blue"], fill="tozeroy")

        # Define figure layout
        layout = go.Layout(
            margin=dict(t=50, r=0, b=10, l=0),
            showlegend=False,
            xaxis=dict(rangeslider={"visible": False}, title="m/z"),
            yaxis=dict(fixedrange=True, title="Intensity"),
            template="plotly_dark",
            title={
                "text": "High resolution spectrum (averaged across pixels)",
                "y": 0.92,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
                "font": dict(
                    size=14,
                ),
            },
            paper_bgcolor="rgba(0,0,0,0.3)",
            plot_bgcolor="rgba(0,0,0,0.3)",
        )
        # Build figure layout
        fig = go.Figure(data=data, layout=layout)

        # Annotate selected lipids with vertical bars
        if annotations is not None:
            for color, x in zip(["red", "green", "blue"], annotations):
                if x is not None:
                    if x[0] >= lb and x[-1] <= hb:
                        fig.add_vrect(
                            x0=x[0], x1=x[1], line_width=0, fillcolor=dic_colors[color], opacity=0.4
                        )

        # In case we don't want to zoom in too much on the selected lipid
        if force_xlim:
            fig.update_xaxes(range=[lb, hb])
        return fig

    def return_empty_spectrum(self):
        """This function returns an empty spectrum, used to display when no spectrum is available.

        Returns:
            Plotly Figure: A Plotly Figure representing an empty spectrum."""

        # Define empty figure data
        data = (go.Scattergl(x=[], y=[], visible=True),)

        # Define figure layout
        layout = go.Layout(
            margin=dict(t=5, r=0, b=10, l=0),
            showlegend=True,
            xaxis=dict(title="m/z"),
            yaxis=dict(title="Intensity"),
            template="plotly_dark",
        )

        # Build figure
        fig = go.Figure(data=data, layout=layout)

        # Transparent background
        fig.layout.plot_bgcolor = "rgba(0,0,0,0)"
        fig.layout.paper_bgcolor = "rgba(0,0,0,0)"
        return fig

    # ==============================================================================================
    # --- Methods used mainly in region_analysis
    # ==============================================================================================

    def return_heatmap_lipid(self, fig=None):
        """This function is used to either generate a Plotly Figure containing an empty go.Heatmap,
        or complete the figure passed as argument with a proper layout that matches the theme of the
        app.

        Args:
            fig (Plotly Figure, optional): A Plotly Figure whose layout must be completed. If None,
                a new figure will be generated. Defaults to None.

        Returns:
            Plotly Figure: A Plotly Figure containing an empty go.Heatmap, or complete the figure
                passed as argument with a proper layout that matches the theme of the app.
        """

        # Build empty figure if not provided
        if fig is None:
            fig = go.Figure(data=go.Heatmap(z=[[]], x=[], y=[], visible=False))

        # Improve figure layout
        fig.update_layout(
            margin=dict(t=25, r=0, b=10, l=0),
            template="plotly_dark",
            font_size=8,
        )

        # Transparent background
        fig.layout.plot_bgcolor = "rgba(0,0,0,0)"
        fig.layout.paper_bgcolor = "rgba(0,0,0,0)"

        # Dark Template
        fig.layout.template = "plotly_dark"

        return fig

    # ==============================================================================================
    # --- Methods used mainly in threeD_exploration
    # ==============================================================================================

    def compute_treemaps_figure(self, maxdepth=5):
        """This function is used to generate a Plotly Figure containing a treemap of the Allen Brain
        Atlas hierarchy.

        Args:
            maxdepth (int, optional): The depth of the treemap to generate. Defaults to 5.

        Returns:
            Plotly.Figure: A Plotly Figure containing a treemap of the Allen Brain Atlas hierarchy.
        """

        # Build treemaps from list of children and parents
        fig = px.treemap(
            names=self._atlas.l_nodes, parents=self._atlas.l_parents, maxdepth=maxdepth
        )

        # Improve layout
        fig.update_layout(
            uniformtext=dict(minsize=15),
            margin=dict(t=30, r=0, b=10, l=0),
        )
        fig.update_traces(root_color="#1d3d5c")

        # Set background color to zero
        fig.layout.template = "plotly_dark"
        fig.layout.plot_bgcolor = "rgba(0,0,0,0)"
        fig.layout.paper_bgcolor = "rgba(0,0,0,0)"

        return fig

    def compute_3D_root_volume(self, decrease_dimensionality_factor=7):
        """This function is used to generate a go.Isosurface of the Allen Brain root structure,
        which will be used to enclose the display of lipid expression of other structures in the
        brain.

        Args:
            decrease_dimensionality_factor (int, optional): Decrease the dimensionnality of the
                brain to display, to get a lighter output. Defaults to 7.

        Returns:
            go.Isosurface: A semi-transparent go.Isosurface of the Allen Brain root structure.
        """
        # Get array of annotations, which associate coordinate to id
        array_annotation_root = np.array(self._atlas.bg_atlas.annotation, dtype=np.int32)

        # Subsample array of annotation the same way array_atlas was subsampled
        array_annotation_root = array_annotation_root[
            ::decrease_dimensionality_factor,
            ::decrease_dimensionality_factor,
            ::decrease_dimensionality_factor,
        ]

        # Bug correction for the last slice
        array_annotation_root = np.concatenate(
            (
                array_annotation_root,
                np.zeros((1, array_annotation_root.shape[1], array_annotation_root.shape[2])),
            )
        )

        # Get the volume array
        array_atlas_borders_root = fill_array_borders(
            array_annotation_root,
            differentiate_borders=False,
            color_near_borders=False,
            keep_structure_id=None,
        )

        # Compute the 3D grid
        X_root, Y_root, Z_root = np.mgrid[
            0 : array_atlas_borders_root.shape[0]
            / 1000
            * 25
            * decrease_dimensionality_factor : array_atlas_borders_root.shape[0]
            * 1j,
            0 : array_atlas_borders_root.shape[1]
            / 1000
            * 25
            * decrease_dimensionality_factor : array_atlas_borders_root.shape[1]
            * 1j,
            0 : array_atlas_borders_root.shape[2]
            / 1000
            * 25
            * decrease_dimensionality_factor : array_atlas_borders_root.shape[2]
            * 1j,
        ]

        # Compute the plot
        brain_root_data = go.Isosurface(
            x=X_root.flatten(),
            y=Y_root.flatten(),
            z=Z_root.flatten(),
            value=array_atlas_borders_root.flatten(),
            isomin=-0.21,
            isomax=2.55,
            opacity=0.1,  # max opacity
            surface_count=2,
            colorscale="Blues",  # colorscale,
            flatshading=True,
            showscale=False,
        )

        return brain_root_data

    def get_array_of_annotations(self, decrease_dimensionality_factor):
        """This function returns the array of annotations from the Allen Brain Atlas, subsampled to
        decrease the size of the output.
        Args:
            decrease_dimensionality_factor (int): An integer used for subsampling the array. The
            higher, the higher the subsampling.

        Returns:
            np.ndarray: A 3D array of annotation, in which structures are annotated with specific
                identifiers.
        """
        # Get subsampled array of annotations
        array_annotation = np.array(
            self._atlas.bg_atlas.annotation[
                ::decrease_dimensionality_factor,
                ::decrease_dimensionality_factor,
                ::decrease_dimensionality_factor,
            ],
            dtype=np.int32,
        )

        # Bug correction for the last slice
        array_annotation = np.concatenate(
            (
                array_annotation,
                np.zeros((1, array_annotation.shape[1], array_annotation.shape[2])),
            )
        )

        return array_annotation

    def compute_l_array_2D(
        self, ll_t_bounds, normalize_independently=True, high_res=False, cache_flask=None
    ):
        """This function is used to get the list of expression per slice for all slices for the
        computation of the 3D brain volume.

        Args:
            ll_t_bounds (list(list(tuple))): A list of lists of lipid boundaries (tuples). The first
                list is used to separate image channels. The second list is used to separate lipid.
            normalize_independently (bool, optional): If True, each lipid intensity array is
                normalized independently, regardless of other lipids or channel used. Defaults to
                True.
            high_res (bool, optional): If True, the returned list of arrays correspond to the
                warped/upscaled data. Defaults to False as this is a very heavy plot.
            cache_flask (flask_caching.Cache, optional): Cache of the Flask database. If set to
                None, the reading of memory-mapped data will not be multithreads-safe. Defaults to
                None.
        Returns:
            list(np.ndarray): A list of numpy arrays representing the expression of the requested
                lipids (through ll_t_bounds) for each slice.
        """
        l_array_data = []

        for slice_index in range(0, self._data.get_slice_number(), 1):

            if ll_t_bounds[slice_index] != [None, None, None]:

                # Get the data as an expression image per lipid
                array_data = self.compute_rgb_array_per_lipid_selection(
                    slice_index + 1,
                    ll_t_bounds[slice_index],
                    normalize_independently=normalize_independently,
                    projected_image=high_res,
                    log=False,
                    apply_transform=True,
                    cache_flask=cache_flask,
                )

                # Sum array colors (i.e. lipids)
                array_data = np.sum(array_data, axis=-1)
            else:
                array_data = None

            # Append data to l_array_data
            l_array_data.append(np.array(array_data, dtype=np.float16))  # float16 to gain space

        return l_array_data

    def compute_array_coordinates_3D(
        self,
        l_array_data,
        high_res=False,
    ):
        """This functions computes the list of coordinates and expression values for the voxels used
        in the 3D representation of the brain.

        Args:
            l_array_data (list(np.ndarray)): A list of numpy arrays representing lipid expression
                for each slice of the dataset.
            high_res (bool, optional): If True, the computations made correspond to the
                warped/upscaled data. Defaults to False as this is a very heavy plot.
        Returns:
            np.ndarray, np.ndarray, np.ndarray, np.ndarray: 4 flat numpy arrays (3 for coordinates
                and 1 for expression).
        """

        logging.info("Starting computing 3D arrays" + logmem())

        # get list of original coordinates for each slice
        if not high_res:
            l_coor = self._atlas.l_original_coor
            estimate = 400 * 400
        else:
            estimate = 1311 * 918
            l_coor = self._atlas.array_coordinates_warped_data

        # Initialize empty arrays with a large estimate for the orginal acquisition size

        max_size = estimate * self._data.get_slice_number()
        array_x = np.empty(max_size, dtype=np.float32)
        array_y = np.empty(max_size, dtype=np.float32)
        array_z = np.empty(max_size, dtype=np.float32)
        array_c = np.empty(max_size, dtype=np.int16)
        total_index = 0
        logging.debug(f"Size array_x: {array_x.nbytes / 1024 / 1024 :.2f}")
        logging.info("Starting slice iteration" + logmem())

        # get atlas shape and resolution
        reference_shape = self._atlas.bg_atlas.reference.shape
        resolution = self._atlas.resolution
        array_annotations = np.array(self._atlas.bg_atlas.annotation, dtype=np.int32)

        for slice_index in range(0, self._data.get_slice_number(), 1):

            # Get the averaged expression data for the current slice
            array_data = l_array_data[slice_index]

            # If array_data is not an array but a 0 float, skip it
            if type(array_data) == float:
                continue

            # Remove pixels for which lipid expression is zero
            array_data_stripped = array_data.flatten()  # array_data[array_data != 0].flatten()

            # Skip the current slice if expression is very sparse
            if len(array_data_stripped) < 10 or np.sum(array_data_stripped) < 1:
                continue

            # Compute the percentile of expression to filter out lowly expressed pixels
            # Set to 0 for now, as no filtering is done
            percentile = 0  # np.percentile(array_data_stripped, 10)

            # Get the coordinates of the pixels in the ccfv3
            coordinates = l_coor[slice_index]
            # coordinates_stripped = coordinates[array_data != 0]
            coordinates_stripped = coordinates.reshape(-1, coordinates.shape[-1])

            # Get the data as 4 arrays (3 for coordinates and 1 for expression)
            array_x, array_y, array_z, array_c, total_index = filter_voxels(
                array_data_stripped.astype(np.float32),
                coordinates_stripped,
                array_annotations,
                percentile,
                array_x,
                array_y,
                array_z,
                array_c,
                total_index,
                reference_shape,
                resolution,
            )
            logging.info("Slice " + str(slice_index) + " done" + logmem())

        # Strip the arrays from the zeros
        array_x = array_x[:total_index]
        array_y = array_y[:total_index]
        array_z = array_z[:total_index]
        # * Caution, array_c should be a list to work with Plotly
        array_c = array_c[:total_index].tolist()

        # Return the arrays for the 3D figure
        return array_x, array_y, array_z, array_c

    def compute_3D_volume_figure(
        self,
        ll_t_bounds,
        name_lipid_1="",
        name_lipid_2="",
        name_lipid_3="",
        set_id_regions=None,
        decrease_dimensionality_factor=6,
        cache_flask=None,
    ):
        """This figure computes a Plotly Figure containing a go.Volume object representing the
        expression of the requested lipids in the selected regions, interpolated between the slices.
        Lipid names are used to retrieve the expression data from the Shelve database.

        Args:
            ll_t_bounds (list(list(tuple))): A list of lists of lipid boundaries (tuples). The first
                list is used to separate image channels. The second list is used to separate lipid.
            name_lipid_1 (str, optional): Name of the first selected lipid. Defaults to "".
            name_lipid_2 (str, optional): Name of the second selected lipid. Defaults to "".
            name_lipid_3 (str, optional): Name of the third selected lipid. Defaults to "".
            set_id_regions (set(int), optional): A set containing the identifiers of the brain
                regions (at the very bottom of the hierarchy) whose border must be annotated.
                Defaults to None, corresponding to the whole brain.
            decrease_dimensionality_factor (int): An integer used for subsampling the array of
                annotation, and therefore the resulting figure. The higher, the higher the
                subsampling. Needed as this is a very heavy plot. Defaults to 6.
            cache_flask (flask_caching.Cache, optional): Cache of the Flask database. If set to
                None, the reading of memory-mapped data will not be multithreads-safe. Defaults to
                None.
        Returns:
            go.Figure: A Plotly Figure containing a go.Volume object representing the expression of
                the requested lipids in the selected regions, interpolated between the slices.
        """
        logging.info("Starting 3D volume computation")

        # Get subsampled array of annotations
        array_annotation = self._storage.return_shelved_object(
            "figures/3D_page",
            "arrays_annotation",
            force_update=False,
            compute_function=self.get_array_of_annotations,
            decrease_dimensionality_factor=decrease_dimensionality_factor,
        )

        # Get subsampled array of borders for each region
        array_atlas_borders = np.zeros(array_annotation.shape, dtype=np.float32)
        list_id_regions = np.array(list(set_id_regions), dtype=np.int64)

        # Shelving this function is useless as it takes less than 0.1s to compute after
        # first compilation
        array_atlas_borders = fill_array_borders(
            array_annotation,
            keep_structure_id=list_id_regions,
            decrease_dimensionality_factor=decrease_dimensionality_factor,
        )

        logging.info("Computed basic structure array")

        # Get array of expression for each lipid
        ll_array_data = [
            self._storage.return_shelved_object(
                "figures/3D_page",
                "arrays_expression_" + str(name_lipid) + "__",
                force_update=False,
                ignore_arguments_naming=True,
                compute_function=self.compute_l_array_2D,
                ll_t_bounds=[[l_t_bounds[i], None, None] for l_t_bounds in ll_t_bounds],
                cache_flask=cache_flask,
            )
            for i, name_lipid in enumerate([name_lipid_1, name_lipid_2, name_lipid_3])
        ]

        # Average array of expression over lipid
        l_array_data_avg = []
        for slice_index in range(0, self._data.get_slice_number(), 1):
            n = 0
            avg = 0
            for i in range(3):  # * number of lipids is hardcoded
                s = ll_array_data[i][slice_index]
                if s is None:
                    s = 0
                else:
                    n += 1
                avg += s

            # In case there's no data for the current slice, set the average to 0
            if n == 0:
                n = 1
            l_array_data_avg.append(avg / n)
        logging.info("Averaged expression over all lipids")

        # Get the 3D array of expression and coordinates
        array_x, array_y, array_z, array_c = self.compute_array_coordinates_3D(
            l_array_data_avg, high_res=False
        )

        logging.info("Computed array of expression in original space")

        # Compute the rescaled array of expression for each slice averaged over projected lipids
        array_slices = np.copy(array_atlas_borders)
        array_for_avg = np.full_like(array_atlas_borders, 1)
        array_x_scaled = array_x * 1000000 / self._atlas.resolution / decrease_dimensionality_factor
        array_y_scaled = array_y * 1000000 / self._atlas.resolution / decrease_dimensionality_factor
        array_z_scaled = array_z * 1000000 / self._atlas.resolution / decrease_dimensionality_factor

        array_slices = fill_array_slices(
            array_x_scaled,
            array_y_scaled,
            array_z_scaled,
            np.array(array_c),
            array_slices,
            array_for_avg,
            limit_value_inside=-1.99999,
        )
        logging.info("Filled basic structure array with array of expression")

        # Get the corresponding coordinates
        X, Y, Z = np.mgrid[
            0 : array_atlas_borders.shape[0]
            / 1000
            * 25
            * decrease_dimensionality_factor : array_atlas_borders.shape[0]
            * 1j,
            0 : array_atlas_borders.shape[1]
            / 1000
            * 25
            * decrease_dimensionality_factor : array_atlas_borders.shape[1]
            * 1j,
            0 : array_atlas_borders.shape[2]
            / 1000
            * 25
            * decrease_dimensionality_factor : array_atlas_borders.shape[2]
            * 1j,
        ]
        logging.info("Built arrays of coordinates")
        if set_id_regions is not None:
            x_min, x_max, y_min, y_max, z_min, z_max = crop_array(array_annotation, list_id_regions)
            array_annotation = array_annotation[
                x_min : x_max + 1, y_min : y_max + 1, z_min : z_max + 1
            ]
            array_slices = array_slices[x_min : x_max + 1, y_min : y_max + 1, z_min : z_max + 1]
            X = X[x_min : x_max + 1, y_min : y_max + 1, z_min : z_max + 1]
            Y = Y[x_min : x_max + 1, y_min : y_max + 1, z_min : z_max + 1]
            Z = Z[x_min : x_max + 1, y_min : y_max + 1, z_min : z_max + 1]
            logging.info("Cropped the figure to only keep areas in which lipids are expressed")

        # Compute an array containing the lipid expression interpolated for every voxel
        array_interpolated = fill_array_interpolation(
            array_annotation,
            array_slices,
            divider_radius=16,
            limit_value_inside=-1.99999,
        )
        logging.info("Finished interpolation between slices")

        # Get root figure
        root_data = self._storage.return_shelved_object(
            "figures/3D_page",
            "volume_root",
            force_update=False,
            compute_function=self.compute_3D_root_volume,
        )

        logging.info("Building final figure")

        # Build figure
        fig = go.Figure(
            data=[
                go.Volume(
                    x=X.flatten(),
                    y=Y.flatten(),
                    z=Z.flatten(),
                    value=array_interpolated.flatten(),
                    isomin=0.01,
                    isomax=1.5,
                    opacityscale=[
                        [-0.11, 0.00],
                        [0.01, 0.0],
                        [0.5, 0.05],
                        [2.5, 0.7],
                    ],
                    surface_count=10,
                    colorscale="viridis",
                ),
                root_data,
            ]
        )

        # Hide grey background
        fig.update_layout(
            margin=dict(t=0, r=0, b=0, l=0),
            scene=dict(
                xaxis=dict(backgroundcolor="rgba(0,0,0,0)"),
                yaxis=dict(backgroundcolor="rgba(0,0,0,0)"),
                zaxis=dict(backgroundcolor="rgba(0,0,0,0)"),
            ),
        )

        # Set background color to zero
        fig.layout.template = "plotly_dark"
        fig.layout.plot_bgcolor = "rgba(0,0,0,0)"
        fig.layout.paper_bgcolor = "rgba(0,0,0,0)"

        logging.info("Done computing 3D volume figure")

        return fig

    def compute_clustergram_figure(
        self, set_progress, cache_flask, l_selected_regions, percentile=90
    ):
        """This function computes a Plotly Clustergram figure, allowing to cluster and compare the
        expression of all the MAIA-transformed lipids in the dataset in the selected regions.

        Args:
            set_progress: Used as part of the Plotly long callbacks, to indicate the progress of the
                computation in the corresponding progress bar.
            cache_flask (flask_caching.Cache, optional): Cache of the Flask database. If set to
                None, the reading of memory-mapped data will not be multithreads-safe. Defaults to
                None.
            l_selected_regions (list(int), optional): A list containing the identifiers of the brain
                regions (at the very bottom of the hierarchy) whose border must be annotated.
            percentile (int, optional): The percentile of average expression below which the lipids
                must be discarded (to get rid of low expression noise). Defaults to 90.

        Returns:
            go.Figure: a Plotly Clustergram figure clustering and comparing the expression of all the
                MAIA-transformed lipids in the dataset in the selected regions.
        """
        logging.info("Starting computing clustergram figure")

        # Memoize result as it's called everytime a filtering is done
        @cache_flask.memoize()
        def return_df_avg_lipids(l_selected_regions):
            dic_avg_lipids = {}
            for slice_index in range(self._data.get_slice_number()):

                # Display progress every 10 slices
                if slice_index % 10 == 0:
                    set_progress(
                        (
                            int(slice_index / self._data.get_slice_number() * 100),
                            "Loading slice n°" + str(slice_index + 1),
                        )
                    )

                l_spectra = []
                for region in l_selected_regions:
                    long_region = self._atlas.dic_acronym_name[region]
                    if region in self._atlas.dic_existing_masks[slice_index]:
                        grah_scattergl_data = self._atlas.get_projected_mask_and_spectrum(
                            slice_index, long_region, MAIA_correction=True
                        )[1]
                        l_spectra.append(grah_scattergl_data)
                    else:
                        l_spectra.append(None)
                ll_idx_labels = global_lipid_index_store(self._data, slice_index, l_spectra)
                logging.info("Computing dictionnary for averaging slice " + str(slice_index))

                # Compute average expression for each lipid and each selection
                set_lipids_idx = set()
                ll_lipids_idx = []
                ll_avg_intensity = []
                n_sel = len(l_spectra)
                for spectrum, l_idx_labels in zip(l_spectra, ll_idx_labels):

                    if spectrum is not None:
                        array_intensity_with_lipids = np.array(spectrum, dtype=np.float32)[1, :]
                        array_idx_labels = np.array(l_idx_labels, dtype=np.int32)

                        l_lipids_idx, l_avg_intensity = compute_avg_intensity_per_lipid(
                            array_intensity_with_lipids, array_idx_labels
                        )
                        set_lipids_idx.update(l_lipids_idx)
                    else:
                        l_lipids_idx = None
                        l_avg_intensity = None

                    ll_lipids_idx.append(l_lipids_idx)
                    ll_avg_intensity.append(l_avg_intensity)

                for i, (l_lipids, l_avg_intensity) in enumerate(
                    zip(ll_lipids_idx, ll_avg_intensity)
                ):
                    if l_lipids is not None:
                        for lipid, intensity in zip(l_lipids, l_avg_intensity):
                            if lipid not in dic_avg_lipids:
                                dic_avg_lipids[lipid] = []
                                for j in range(n_sel):
                                    dic_avg_lipids[lipid].append([])
                            dic_avg_lipids[lipid][i].append(intensity)

            logging.info("Averaging all lipid values across slices")

            # Average intensity per slice
            for lipid in dic_avg_lipids:
                for i in range(n_sel):
                    if len(dic_avg_lipids[lipid][i]) > 0:
                        dic_avg_lipids[lipid][i] = np.mean(dic_avg_lipids[lipid][i])
                    else:
                        dic_avg_lipids[lipid][i] = 0

            df_avg_intensity_lipids = pd.DataFrame.from_dict(
                dic_avg_lipids,
                orient="index",
                columns=[l_selected_regions[i] for i in range(n_sel)],
            )
            return df_avg_intensity_lipids

        df_avg_intensity_lipids = return_df_avg_lipids(l_selected_regions)
        logging.info("Averaging done for all slices")
        set_progress((90, "Loading data"))

        # Exclude very lowly expressed lipids
        df_min_expression = df_avg_intensity_lipids.min(axis=1)
        df_avg_intensity_lipids = df_avg_intensity_lipids[
            df_min_expression > df_min_expression.quantile(q=int(percentile) / 100)
        ]

        if len(l_selected_regions) > 1:
            df_avg_intensity_lipids = df_avg_intensity_lipids.iloc[
                (df_avg_intensity_lipids.mean(axis=1)).argsort(), :
            ]
        else:
            df_avg_intensity_lipids.sort_values(by=l_selected_regions[0], inplace=True)
        logging.info("Lowly expressed lipids excluded")

        # Replace idx_lipids by actual name
        df_names = self._data.get_annotations()
        df_avg_intensity_lipids.index = df_avg_intensity_lipids.index.map(
            lambda idx: df_names.iloc[idx]["name"]
            + "_"
            + df_names.iloc[idx]["structure"]
            + "_"
            + df_names.iloc[idx]["cation"]
        )
        logging.info("Lipid indexes replaced by names")
        logging.info("Preparing plot")
        # Plot
        fig_heatmap_lipids = Clustergram(
            data=df_avg_intensity_lipids.to_numpy(),
            column_labels=df_avg_intensity_lipids.columns.to_list(),
            row_labels=df_avg_intensity_lipids.index.to_list(),
            hidden_labels="row" if len(df_avg_intensity_lipids.index.to_list()) > 100 else None,
            color_map="Viridis",
            height=800,
            width=1000,
            display_ratio=[0.2, 0.01],
        )

        # Set background color to zero
        fig_heatmap_lipids.layout.template = "plotly_dark"
        fig_heatmap_lipids.layout.plot_bgcolor = "rgba(0,0,0,0)"
        fig_heatmap_lipids.layout.paper_bgcolor = "rgba(0,0,0,0)"

        set_progress((100, "Returning figure"))
        logging.info("Returning figure")
        return fig_heatmap_lipids

    # ==============================================================================================
    # --- Methods used for shelving results
    # ==============================================================================================

    def shelve_arrays_basic_figures(self, force_update=False):
        """This function shelves in the database all the arrays of basic images computed in
        self.compute_figure_basic_image(), across all slices and all types of arrays. This forces
        the precomputations of these arrays, and allows to access them faster. Once everything has
        been shelved, a boolean value is stored in the shelve database, to indicate that the arrays
        do not need to be recomputed at next app startup.

        Args:
            force_update (bool, optional): If True, the function will not overwrite existing files.
                Defaults to False.
        """
        for idx_slice in range(self._data.get_slice_number()):
            for type_figure in ["original_data", "warped_data", "projection_corrected", "atlas"]:
                for display_annotations in [True, False]:

                    # Force no annotation for the original data
                    self._storage.return_shelved_object(
                        "figures/load_page",
                        "figure_basic_image",
                        force_update=force_update,
                        compute_function=self.compute_figure_basic_image,
                        type_figure=type_figure,
                        index_image=idx_slice,
                        plot_atlas_contours=display_annotations
                        if type_figure != "original_data"
                        else False,
                    )

        self._storage.dump_shelved_object(
            "figures/load_page", "arrays_basic_figures_computed", True
        )

    # ! Need to update for brain 2 as well

    def shelve_all_l_array_2D(self, force_update=False, sample=False):
        """This functions precomputes and shelves all the arrays of lipid expression used in a 3D
        representation of the brain (through self.compute_3D_volume_figure()). Once everything has
        been shelved, a boolean value is stored in the shelve database, to indicate that the arrays
        do not need to be recomputed at next app startup.

        Args:
            force_update (bool, optional): If True, the function will not overwrite existing files.
                Defaults to False.
            sample (bool, optional): If True, only a fraction of the precomputations are made (for
                debug). Default to False.
        """

        # Count number of lipids processed for sampling
        n_processed = 0
        if sample:
            logging.warning("Only a sample of the lipid arrays will be computed!")

        # Simulate a click on all lipid names
        for name in sorted(
            self._data.get_annotations_MAIA_transformed_lipids(brain_1=True).name.unique()
        ):
            structures = self._data.get_annotations_MAIA_transformed_lipids(brain_1=True)[
                self._data.get_annotations_MAIA_transformed_lipids(brain_1=True)["name"] == name
            ].structure.unique()
            for structure in sorted(structures):
                cations = self._data.get_annotations_MAIA_transformed_lipids(brain_1=True)[
                    (
                        self._data.get_annotations_MAIA_transformed_lipids(brain_1=True)["name"]
                        == name
                    )
                    & (
                        self._data.get_annotations_MAIA_transformed_lipids(brain_1=True)[
                            "structure"
                        ]
                        == structure
                    )
                ].cation.unique()
                for cation in sorted(cations):
                    l_selected_lipids = []
                    for slice_index in range(self._data.get_slice_number()):

                        # Find lipid location
                        l_lipid_loc = (
                            self._data.get_annotations()
                            .index[
                                (self._data.get_annotations()["name"] == name)
                                & (self._data.get_annotations()["structure"] == structure)
                                & (self._data.get_annotations()["slice"] == slice_index)
                                & (self._data.get_annotations()["cation"] == cation)
                            ]
                            .tolist()
                        )

                        # If several lipids correspond to the selection, we have a problem...
                        if len(l_lipid_loc) > 1:
                            logging.warning("More than one lipid corresponds to the selection")
                            l_lipid_loc = [l_lipid_loc[-1]]
                        # If no lipid correspond to the selection, set to -1
                        if len(l_lipid_loc) == 0:
                            l_lipid_loc = [-1]

                        # add lipid index for each slice
                        l_selected_lipids.append(l_lipid_loc[0])

                    # Get final lipid name
                    lipid_string = name + " " + structure + " " + cation

                    # If lipid is present in at least one slice
                    if np.sum(l_selected_lipids) > -self._data.get_slice_number():

                        # Build the list of mz boundaries for each peak and each index
                        lll_lipid_bounds = [
                            [
                                [
                                    (
                                        float(self._data.get_annotations().iloc[index]["min"]),
                                        float(self._data.get_annotations().iloc[index]["max"]),
                                    )
                                ]
                                if index != -1
                                else None
                                for index in [lipid_1_index, -1, -1]
                            ]
                            for lipid_1_index in l_selected_lipids
                        ]

                        # Compute 3D figures, selection is limited to one lipid
                        name_lipid = lipid_string

                        self._storage.return_shelved_object(
                            "figures/3D_page",
                            "arrays_expression_" + name_lipid + "__",
                            force_update=force_update,
                            compute_function=self.compute_l_array_2D,
                            ignore_arguments_naming=True,
                            ll_t_bounds=lll_lipid_bounds,
                            cache_flask=None,  # No cache needed since launched at startup
                        )

                        n_processed += 1
                        if n_processed >= 10 and sample:
                            return None

        # Variable to signal everything has been computed
        self._storage.dump_shelved_object("figures/3D_page", "arrays_expression_computed", True)

    def shelve_all_arrays_annotation(self):
        """This functions precomputes and shelves the array of structure annotation used in a
        3D representation of the brain (through self.compute_3D_volume_figure()), at different
        resolutions. Once everything has been shelved, a boolean value is stored in the shelve
        database, to indicate that the arrays do not need to be recomputed at next app startup.
        """
        for decrease_dimensionality_factor in range(2, 13):
            self._storage.return_shelved_object(
                "figures/3D_page",
                "arrays_annotation",
                force_update=False,
                compute_function=self.get_array_of_annotations,
                decrease_dimensionality_factor=decrease_dimensionality_factor,
            )

        # Variable to signal everything has been computed
        self._storage.dump_shelved_object("figures/3D_page", "arrays_annotation_computed", True)
