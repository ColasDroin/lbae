###### IMPORT MODULES ######

# Standard modules
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os
from skimage import io
from scipy.ndimage.interpolation import map_coordinates
import logging
from numba import njit
import pandas as pd
import dash_bio as dashbio

# Homemade functions
from modules.tools import spectra
from modules.tools.image import convert_image_to_base64
from modules.tools.storage import return_shelved_object
from modules.tools.atlas import project_image, slice_to_atlas_transform
from modules.tools.misc import logmem
from modules.tools.volume import filter_voxels, fill_array_borders, fill_array_interpolation
from config import dic_colors, l_colors, l_colors_progress
from modules.tools.spectra import compute_avg_intensity_per_lipid, global_lipid_index_store

###### DEFINE FIGURES CLASS ######
class Figures:
    __slots__ = ["_data", "_atlas", "dic_fig_contours", "dic_normalization_factors"]

    def __init__(self, maldi_data, atlas):
        logging.info("Initializing Figures object" + logmem())
        self._data = maldi_data
        self._atlas = atlas

        # Dic of basic contours figure (must be ultra fast because used with hovering)
        self.dic_fig_contours = return_shelved_object(
            "figures/region_analysis",
            "dic_fig_contours",
            force_update=False,
            compute_function=self.compute_dic_fig_contours,
        )

        # Dic of normalization factors across slices for MAIA normalized lipids
        self.dic_normalization_factors = return_shelved_object(
            "figures/lipid_selection",
            "dic_normalization_factors",
            force_update=False,
            compute_function=self.compute_normalization_factor_across_slices,
        )

    ###### FUNCTIONS FOR FIGURE IN LOAD_SLICE PAGE ######

    # ? Move into another class? Doesn't really need self
    def compute_padded_original_images(self):

        # Compute number of slices from the original acquisition are present in the folder
        path = "data/tiff_files/original_data/"
        n_slices = len([x for x in os.listdir(path) if "slice_" in x])
        if n_slices != self._data.get_slice_number():
            logging.warning(
                "The number of slices computed from the original tiff files is different from the number of slice "
                + "recorded in the MaldiData object."
            )

        # Store them as arrays in a list
        l_array_slices = []
        for i in range(n_slices):
            filename = path + "slice_" + str(i + 1) + ".tiff"
            l_array_slices.append(np.array(io.imread(filename), dtype=np.int16)[:, :, 2])

        # Find the size of the biggest image
        max_size = (
            np.max([array_slice.shape[0] for array_slice in l_array_slices]),
            np.max([array_slice.shape[1] for array_slice in l_array_slices]),
        )

        # Pad the images with zeros (we add +-0.1 in case we need to round above or below 0.5 if odd dimension)
        l_array_slices = [
            np.pad(
                array_slice,
                (
                    (
                        int(round(max_size[0] - array_slice.shape[0] / 2 - 0.1)),
                        int(round(max_size[0] - array_slice.shape[0] / 2 + 0.1)),
                    ),
                    (
                        int(round(max_size[1] - array_slice.shape[1] / 2 - 0.1)),
                        int(round(max_size[1] - array_slice.shape[1] / 2 + 0.1)),
                    ),
                ),
            )
            for array_slice in l_array_slices
        ]

        return np.array(l_array_slices)

    # For docstring: if only_contours is True, all other arguments (but index_image) are ignored
    def compute_figure_basic_image(
        self, type_figure, index_image, plot_atlas_contours=True, only_contours=False, draw=False
    ):

        # If only boundaries is requested, force the computation of atlas contours
        if only_contours:
            plot_atlas_contours = True

        else:
            # Get array of images
            array_images = return_shelved_object(
                "figures/load_page",
                "array_basic_images",
                force_update=False,
                compute_function=self.compute_array_basic_images,
                type_figure=type_figure,
            )

            array_image = array_images[index_image]

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
            # fig.update_yaxes(
            #    title_text=self._atlas.bg_atlas.space.axis_labels[0][0], title_standoff=0
            # )

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

    # This function is needed to hover fast when manually selecting regions
    def compute_dic_fig_contours(self):
        dic = {}
        for slice_index in range(self._data.get_slice_number()):
            fig = return_shelved_object(
                "figures/load_page",
                "figure_basic_image",
                force_update=False,
                compute_function=self.compute_figure_basic_image,
                type_figure=None,
                index_image=slice_index,
                plot_atlas_contours=True,
                only_contours=True,
            )
            dic[slice_index] = fig
        return dic

    def compute_array_basic_images(self, type_figure="warped_data"):
        array_images = None
        if type_figure == "original_data":
            array_images = self.compute_padded_original_images()
        elif type_figure == "warped_data":
            array_images = np.array(io.imread("data/tiff_files/warped_data.tif"))
        elif type_figure == "projection_corrected":
            array_images = self._atlas.array_projection_corrected
        elif type_figure == "atlas":
            array_projected_images_atlas, array_projected_simplified_id = return_shelved_object(
                "atlas/atlas_objects",
                "array_images_atlas",
                force_update=False,
                compute_function=self._atlas.compute_array_images_atlas,
                zero_out_of_annotation=True,
            )
            array_images = array_projected_images_atlas
        return array_images

    # ? Drop this function as well? But this one works and may be kept in the future
    def compute_figure_basic_images_with_slider(
        self, type_figure="warped_data", plot_atlas_contours=False
    ):
        # Get array of images
        array_images = return_shelved_object(
            "figures/load_page",
            "array_basic_images",
            force_update=False,
            compute_function=self.compute_array_basic_images,
            type_figure=type_figure,
        )

        if plot_atlas_contours:
            array_images_atlas = self._atlas.list_projected_atlas_borders_arrays

        # Build plot with slider
        fig = go.Figure(
            frames=[
                go.Frame(
                    data=[
                        go.Image(
                            visible=True,
                            source=convert_image_to_base64(
                                array_images[i],
                                overlay=array_images_atlas[i] if plot_atlas_contours else None,
                                optimize=True,
                                quality=40,
                            ),
                            hoverinfo="none",
                        ),
                        # array_images_atlas[i],
                    ],
                    name=str(i + 1),
                )
                for i in range(0, self._data.get_slice_number(), 1)
            ]
        )
        fig.add_trace(
            go.Image(
                visible=True,
                source=convert_image_to_base64(
                    array_images[0],
                    overlay=array_images_atlas[0] if plot_atlas_contours else None,
                    optimize=True,
                    quality=40,
                ),
                hoverinfo="none",
            )
        )

        # fig.add_trace(array_images_atlas[0],)

        def frame_args(duration):
            return {
                "frame": {"duration": duration},
                "mode": "immediate",
                "fromcurrent": True,
                "transition": {"duration": duration, "easing": "linear"},
            }

        sliders = [
            {
                "pad": {"b": 10, "t": 60},
                "len": 0.9,
                "x": 0.1,
                "y": 0,
                "steps": [
                    {"args": [[f.name], frame_args(0)], "label": str(k), "method": "update",}
                    for k, f in enumerate(fig.frames)
                ],
            }
        ]

        # Layout
        fig.update_layout(margin=dict(t=25, r=0, b=0, l=0),)

        def frame_args(duration):
            return {
                "frame": {"duration": duration, "redraw": True},
                "mode": "immediate",
                "fromcurrent": True,
                "transition": {"duration": duration, "easing": "linear"},
            }

        fig.layout.sliders = [
            {
                "active": 0,
                "yanchor": "top",
                "xanchor": "left",
                "currentvalue": {"prefix": "Slice" + "="},
                "pad": {"b": 10, "t": 60},
                "len": 0.9,
                "x": 0.1,
                "y": 0,
                "steps": [
                    {"args": [[f.name], frame_args(0)], "label": f.name, "method": "animate",}
                    for f in fig.frames
                ],
            }
        ]

        logging.info("Figure has been computed")
        return fig

    ###### FUNCTIONS FOR FIGURE IN LIPID_SELECTION PAGE ######

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
    ):
        logging.info("Entering compute_image_per_lipid")
        # Get image from raw mass spec data
        image = spectra.compute_image_using_index_and_image_lookup(
            lb_mz,
            hb_mz,
            self._data.get_array_spectra(slice_index),
            self._data.get_array_lookup_pixels(slice_index),
            self._data.get_image_shape(slice_index),
            self._data.get_array_lookup_mz(slice_index),
            self._data.get_array_cumulated_lookup_mz_image(slice_index),
            self._data.get_divider_lookup(slice_index),
            self._data.get_array_peaks_transformed_lipids(slice_index),
            self._data.get_array_corrective_factors(slice_index),
            apply_transform=apply_transform,
        )

        if log:
            image = np.log(image + 1)

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
        if RGB_format:
            image *= 255
        if normalize and RGB_format:
            image = np.round(image).astype(np.uint8)

        # project image into cleaned and higher resolution version
        if projected_image:
            image = project_image(
                slice_index, image, self._atlas.array_projection_correspondence_corrected
            )
        return image

    def compute_normalization_factor_across_slices(self):
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
                    image = spectra.compute_image_using_index_and_image_lookup(
                        lb_mz,
                        hb_mz,
                        self._data.get_array_spectra(slice_index),
                        self._data.get_array_lookup_pixels(slice_index),
                        self._data.get_image_shape(slice_index),
                        self._data.get_array_lookup_mz(slice_index),
                        self._data.get_array_cumulated_lookup_mz_image(slice_index),
                        self._data.get_divider_lookup(slice_index),
                        self._data.get_array_peaks_transformed_lipids(slice_index),
                        self._data.get_array_corrective_factors(slice_index),
                        apply_transform=False,
                    )

                    # check 99th percentile for normalization
                    perc = np.percentile(image, 99.0)
                    # perc must be quite small in theory... otherwise it's a bug
                    if perc > max_perc:  # and perc<1:
                        max_perc = perc

            # Store max percentile across slices
            dic_max_percentile[lipid_string] = max_perc

        return dic_max_percentile

    # ! Check in the end if this function is redundant with compute_heatmap_per_lipid_selection
    def compute_heatmap_per_mz(
        self,
        slice_index,
        lb_mz=None,
        hb_mz=None,
        draw=False,
        binary_string=False,
        projected_image=True,
        plot_contours=False,
        return_base64_string=False,
    ):

        logging.info("Starting figure computation, from mz boundaries")
        if binary_string:
            logging.info(
                "binary_string is set to True, therefore the plot will be made as a heatmap"
            )
            heatmap = True

        # Upper bound lower than the lowest m/z value and higher that the highest m/z value
        if lb_mz is None:
            lb_mz = 200
        if hb_mz is None:
            hb_mz = 1800

        logging.info("Getting image array")
        # Compute image with given bounds
        image = self.compute_image_per_lipid(
            slice_index, lb_mz, hb_mz, RGB_format=True, projected_image=projected_image
        )

        logging.info("Done getting image array. Cleaning memory")
        # Clean memmap memory
        self._data.clean_memory(slice_index=slice_index)
        logging.info("Memory cleaned")

        # Get image
        if plot_contours:
            array_image_atlas = self._atlas.list_projected_atlas_borders_arrays[slice_index - 1]
        else:
            array_image_atlas = None
        logging.info("Converting image to string")
        # Set optimize to False to gain computation time
        base64_string = convert_image_to_base64(
            image, overlay=array_image_atlas, transparent_zeros=True, optimize=False
        )

        # Either return image directly
        if return_base64_string:
            return base64_string

        # Or build graph
        fig = go.Figure()

        logging.info("Adding image to figure")
        fig.add_trace(go.Image(visible=True, source=base64_string))

        # Improve graph layout
        fig.update_layout(
            margin=dict(t=0, r=0, b=0, l=0),
            newshape=dict(
                fillcolor=dic_colors["blue"], opacity=0.7, line=dict(color="white", width=1)
            ),
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False),
            # Do not specify height for now as plotly is buggued and resets it to 450px if switching pages
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

    def compute_heatmap_per_lipid_selection(
        self,
        slice_index,
        ll_t_bounds,
        normalize_independently=True,
        projected_image=True,
        apply_transform=False,
        ll_lipid_names=None,
        return_base64_string=False,
    ):

        logging.info("Compute heatmap per lipid selection" + str(ll_t_bounds))

        # Start from empty image and add selected lipids
        # * Caution: array must be int, float gets badly converted afterwards
        image = np.zeros(self._atlas.image_shape, dtype=np.int32)
        if ll_lipid_names is None:
            ll_lipid_names = [["" for y in l_t_bounds] for l_t_bounds in ll_t_bounds]
        for l_t_bounds, l_lipid_names in zip(ll_t_bounds, ll_lipid_names):
            if l_t_bounds is not None:
                for boundaries, lipid_name in zip(l_t_bounds, l_lipid_names):
                    if boundaries is not None:
                        (lb_mz, hb_mz) = boundaries
                        image_temp = self.compute_image_per_lipid(
                            slice_index,
                            lb_mz,
                            hb_mz,
                            RGB_format=True,
                            normalize=normalize_independently,
                            projected_image=projected_image,
                            apply_transform=apply_transform,
                            lipid_name=lipid_name,
                        )
                        image += image_temp

        # Clean memmap memory
        self._data.clean_memory(slice_index=slice_index)

        # Set optimize to False to gain computation time
        base64_string = convert_image_to_base64(image, transparent_zeros=True, optimize=False)

        # Either return image directly
        if return_base64_string:
            return base64_string

        # Or build graph
        fig = go.Figure()
        fig.add_trace(go.Image(visible=True, source=base64_string))

        # Improve graph layout
        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False),
            margin=dict(t=0, r=0, b=0, l=0),
        )
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)
        fig.update(layout_coloraxis_showscale=False)

        # Set background color to zero
        fig.layout.template = "plotly_dark"
        fig.layout.plot_bgcolor = "rgba(0,0,0,0)"
        fig.layout.paper_bgcolor = "rgba(0,0,0,0)"

        return fig

    def compute_rgb_array_per_lipid_selection(
        self,
        slice_index,
        ll_t_bounds,
        normalize_independently=True,
        projected_image=True,
        log=False,
        enrichment=False,
        apply_transform=False,
        ll_lipid_names=None,
    ):

        # Empty lipid names if no names provided
        if ll_lipid_names is None:
            ll_lipid_names = [
                ["" for y in l_t_bounds] if l_t_bounds is not None else [""]
                for l_t_bounds in ll_t_bounds
            ]

        # Build a list of empty images and add selected lipids for each channel
        l_images = []
        for l_boundaries, l_names in zip(ll_t_bounds, ll_lipid_names):
            image = np.zeros(
                self._atlas.image_shape
                if projected_image
                else self._data.get_image_shape(slice_index)
            )
            if l_boundaries is not None:
                for boundaries, lipid_name in zip(l_boundaries, l_names):
                    if boundaries is not None:
                        (lb_mz, hb_mz) = boundaries

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
                        )

                        image += image_temp

            l_images.append(image)

        # Reoder axis to match plotly go.image requirements
        array_image = np.moveaxis(np.array(l_images), 0, 2)

        # Clean memmap memory
        self._data.clean_memory(slice_index=slice_index)

        return np.asarray(array_image, dtype=np.uint8)

    def compute_rgb_image_per_lipid_selection(
        self,
        slice_index,
        ll_t_bounds,
        normalize_independently=True,
        projected_image=True,
        enrichment=False,
        log=False,
        return_image=False,
        use_pil=True,
        apply_transform=False,
        ll_lipid_names=None,
        return_base64_string=False,
    ):
        logging.info("Started RGB image computation for slice " + str(slice_index) + logmem())

        # Empty lipid names if no names provided
        if ll_lipid_names is None:
            ll_lipid_names = [["" for y in l_t_bounds] for l_t_bounds in ll_t_bounds]

        # Get RGB array for the current lipid selection
        array_image = self.compute_rgb_array_per_lipid_selection(
            slice_index,
            ll_t_bounds,
            normalize_independently=normalize_independently,
            projected_image=projected_image,
            log=log,
            enrichment=enrichment,
            apply_transform=apply_transform,
            ll_lipid_names=ll_lipid_names,
        )
        logging.info("array_image acquired for slice " + str(slice_index) + logmem())

        if use_pil:
            # Set optimize to False to gain computation time
            base64_string_exp = convert_image_to_base64(
                array_image, type="RGB", transparent_zeros=True, optimize=False,
            )
            # Return image directly if needed
            if return_base64_string:
                return base64_string_exp

            final_image = go.Image(visible=True, source=base64_string_exp,)
        else:
            final_image = go.Image(z=array_image)

        if return_image:
            return final_image

        else:
            logging.info("Started building graph for slice " + str(slice_index) + logmem())
            # Build graph from image
            fig = go.Figure(final_image)

            # Improve graph layout
            fig.update_layout(
                xaxis=dict(showgrid=False, zeroline=False),
                yaxis=dict(showgrid=False, zeroline=False),
                margin=dict(t=0, r=0, b=0, l=0),
            )
            fig.update_xaxes(showticklabels=False)
            fig.update_yaxes(showticklabels=False)

            # Set background color to zero
            fig.layout.template = "plotly_dark"
            fig.layout.plot_bgcolor = "rgba(0,0,0,0)"
            fig.layout.paper_bgcolor = "rgba(0,0,0,0)"

            logging.info("Returning fig for slice " + str(slice_index) + logmem())
            return fig

    def compute_spectrum_low_res(self, slice_index, annotations=None):

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
                "font": dict(size=14,),
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
    ):

        # Define default values for graph (empty)
        if lb is None and hb is None:
            x = ([],)
            y = ([],)

        # If boundaries are provided, get their index
        else:
            array_spectra_avg = self._data.get_array_avg_spectrum(
                slice_index, standardization=standardization
            )
            index_lb, index_hb = spectra.compute_index_boundaries(
                lb,
                hb,
                array_spectra_avg=array_spectra_avg,
                lookup_table=self._data.get_array_lookup_mz_avg(slice_index),
            )
            x = array_spectra_avg[0, index_lb:index_hb]
            y = array_spectra_avg[1, index_lb:index_hb]

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
                "font": dict(size=14,),
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

    def return_heatmap_lipid(self, fig=None):

        # Build empty figure if not provided
        if fig is None:
            fig = go.Figure(data=go.Heatmap(z=[[]], x=[], y=[], visible=False))

        # Improve figure layout
        fig.update_layout(
            margin=dict(t=25, r=0, b=10, l=0), template="plotly_dark", font_size=8,
        )

        # Transparent background
        fig.layout.plot_bgcolor = "rgba(0,0,0,0)"
        fig.layout.paper_bgcolor = "rgba(0,0,0,0)"

        return fig

    def compute_figure_slices_3D(self, reduce_resolution_factor=20):

        # get transform parameters (a,u,v) for each slice
        l_transform_parameters = return_shelved_object(
            "atlas/atlas_objects",
            "l_transform_parameters",
            force_update=False,
            compute_function=self._atlas.compute_projection_parameters,
        )

        # reduce resolution of the slices
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
                    {"args": [[f.name], frame_args(0)], "label": str(k), "method": "animate",}
                    for k, f in enumerate(fig.frames)
                ],
                "currentvalue": {"visible": False,},
            }
        ]

        # Layout
        fig.update_layout(
            # title="Experimental slices in volumetric data",
            # width=600,
            # height=600,
            scene=dict(
                # zaxis=dict(autorange=False),
                aspectratio=dict(x=1.5, y=1, z=1),
                # zaxis_autorange="reversed",
                # aspectmode = "data",
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
            margin=dict(t=5, r=0, b=0, l=0),
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

    # ! I can probably numbaize that
    def get_surface(
        self, slice_index, l_transform_parameters, array_projection, reduce_resolution_factor
    ):

        a, u, v = l_transform_parameters[slice_index]

        ll_x = []
        ll_y = []
        ll_z = []

        for i, lambd in enumerate(range(array_projection[slice_index].shape[0])):
            l_x = []
            l_y = []
            l_z = []
            for j, mu in enumerate(range(array_projection[slice_index].shape[1])):
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

            if l_x != []:
                ll_x.append(l_x)
                ll_y.append(l_y)
                ll_z.append(l_z)

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

    def compute_figure_slices_2D(self, ll_t_bounds, normalize_independently=True):

        fig = go.Figure(
            frames=[
                go.Frame(
                    data=self.compute_rgb_image_per_lipid_selection(
                        i,
                        ll_t_bounds[i - 1],
                        normalize_independently=True,
                        title=False,
                        projected_image=True,
                        enrichment=False,
                        log=False,
                        return_image=True,
                        use_pil=True,
                    ),
                    name=str(i),
                )
                for i in range(1, self._data.get_slice_number() + 1, 1)
                if ll_t_bounds[i - 1] != [None, None, None]
            ]
        )

        fig.add_trace(
            self.compute_rgb_image_per_lipid_selection(
                1,
                [
                    ll_t_bounds[i - 1]
                    for i in range(1, self._data.get_slice_number() + 1, 1)
                    if ll_t_bounds[i - 1] != [None, None, None]
                ][0],
                normalize_independently=True,
                title=False,
                projected_image=True,
                enrichment=False,
                log=False,
                return_image=True,
                use_pil=True,
            ),
        )

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
                "x": 0.1,
                "y": 0,
                "steps": [
                    {"args": [[f.name], frame_args(0)], "label": f.name, "method": "animate",}
                    for k, f in enumerate(fig.frames)
                ],
                "currentvalue": {"visible": False,},
            }
        ]

        # Improve graph layout
        fig.update_layout(
            title={
                "text": "",
                "y": 0.97,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
                "font": dict(size=14,),
            },
            margin=dict(t=5, r=0, b=0, l=0),
            # updatemenus=[
            #    {
            #        "buttons": [
            #            {"args": [None, frame_args(50)], "label": "&#9654;", "method": "animate",},  # play symbol
            #            {"args": [[None], frame_args(0)], "label": "&#9724;", "method": "animate",},  # pause symbol
            #        ],
            #        "direction": "left",
            #        "pad": {"r": 10, "t": 10},
            #        "type": "buttons",
            #        "x": 0.1,
            #        "y": 0,
            #    }
            # ],
            sliders=sliders,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)

        return fig

    def compute_array_3D(self, ll_t_bounds, normalize_independently=True, high_res=False):

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
            if ll_t_bounds[slice_index] != [None, None, None]:

                # Get the data as an expression image per lipid
                array_data = self.compute_rgb_array_per_lipid_selection(
                    slice_index + 1,
                    ll_t_bounds[slice_index],
                    normalize_independently=normalize_independently,
                    projected_image=high_res,
                    log=False,
                    enrichment=False,
                    apply_transform=True,
                )

                # Sum array colors (i.e. lipids)
                array_data = np.sum(array_data, axis=-1)
                # Remove pixels for which lipid expression is zero
                # ! Commented temporarily
                # array_data_stripped = array_data[array_data != 0]
                array_data_stripped = array_data.flatten()

                # Skip the current slice if expression is very sparse
                if len(array_data_stripped) < 10 or np.sum(array_data_stripped) < 1:
                    continue

                # Compute the percentile of expression to filter out lowly expressed pixels
                # Set to 0 for now, as no filtering is done
                percentile = 0 #np.percentile(array_data_stripped, 10)

                # Get the coordinates of the pixels in the ccfv3
                coordinates = l_coor[slice_index]
                # ! Same here
                # coordinates_stripped = coordinates[array_data != 0]
                coordinates_stripped = coordinates.reshape(-1, coordinates.shape[-1])

                array_x, array_y, array_z, array_c, total_index = filter_voxels(
                    array_data_stripped,
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
        array_c = array_c[:total_index].tolist()

        # Return the arrays for the 3D figure
        return array_x, array_y, array_z, array_c

    # This function sums over the selected lipids for now
    def compute_figure_bubbles_3D(
        self,
        ll_t_bounds,
        normalize_independently=True,
        high_res=False,
        name_lipid_1="",
        name_lipid_2="",
        name_lipid_3="",
    ):
        logging.info("Starting computing figure bubbles 3D")

        # Get 3D arrays for lipid distribution
        array_x, array_y, array_z, array_c = return_shelved_object(
            "figures/3D_page",
            "arrays_3D_" + name_lipid_1 + "_" + name_lipid_2 + "_" + name_lipid_3,
            force_update=False,
            compute_function=self.compute_array_3D,
            ignore_arguments_naming=True,
            ll_t_bounds=ll_t_bounds,
            normalize_independently=normalize_independently,  # normalize_independently,
            high_res=high_res,
        )

        # Build figure
        fig = go.Figure(
            data=go.Scatter3d(
                x=array_x,
                y=array_y,
                z=array_z,
                mode="markers",
                marker=dict(
                    # sizemode="diameter",
                    # sizeref=40,
                    size=1.5,  # array_c,
                    color=array_c,
                    colorscale="Viridis",
                    reversescale=True,
                    colorbar_title="Expression",
                    # line_color="rgba(140, 140, 170, 0.01)",
                ),
            )
        )
        fig.update_layout(
            scene=dict(
                xaxis=dict(backgroundcolor="rgba(0,0,0,0)", color="grey", gridcolor="grey"),
                yaxis=dict(backgroundcolor="rgba(0,0,0,0)", color="grey", gridcolor="grey"),
                zaxis=dict(backgroundcolor="rgba(0,0,0,0)", color="grey", gridcolor="grey"),
            ),
            margin=dict(t=5, r=0, b=0, l=0),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        logging.info("Done computing 3D bubble figure" + logmem())
        return fig

    def compute_sunburst_figure(self, maxdepth=3):
        fig = px.sunburst(
            names=self._atlas.l_nodes, parents=self._atlas.l_parents, maxdepth=maxdepth
        )
        fig.update_layout(margin=dict(t=0, r=0, b=0, l=0),)
        return fig

    def compute_treemaps_figure(self, maxdepth=5):
        fig = px.treemap(
            names=self._atlas.l_nodes, parents=self._atlas.l_parents, maxdepth=maxdepth
        )
        fig.update_layout(
            uniformtext=dict(minsize=15), margin=dict(t=30, r=0, b=10, l=0),
        )
        fig.update_traces(root_color="#1d3d5c")

        # Set background color to zero
        fig.layout.template = "plotly_dark"
        fig.layout.plot_bgcolor = "rgba(0,0,0,0)"
        fig.layout.paper_bgcolor = "rgba(0,0,0,0)"

        return fig

    def compute_atlas_with_slider(self, view="frontal", contour=False):
        # Check that the given view exists
        if view not in ("frontal", "horizontal", "sagittal"):
            logging.warning(
                "The provided view must be of of the following: frontal, horizontal, or sagittal."
                + "Back to default, i.e. frontal"
            )
            view = "frontal"

        if view == "frontal":
            idx_view = 0
            axis_labels = self._atlas.bg_atlas.space.axis_labels[0]
        elif view == "horizontal":
            idx_view = 1
            axis_labels = self._atlas.bg_atlas.space.axis_labels[1]
        elif view == "sagittal":
            idx_view = 2
            axis_labels = self._atlas.bg_atlas.space.axis_labels[1]

        # multiplier to compute proper slice index depending if contours/mask are present or not
        multiplier = 2 if contour else 1

        # Create figure
        fig = go.Figure()

        subsampling = list(
            range(0, self._atlas.bg_atlas.reference.shape[idx_view], self._atlas.subsampling_block)
        )
        # Add traces, one for each slider step
        for step in subsampling:
            if view == "frontal":
                image_array = self._atlas.bg_atlas.reference[step, :, :]
            elif view == "horizontal":
                image_array = self._atlas.bg_atlas.reference[:, step, :]
            elif view == "sagittal":
                image_array = self._atlas.bg_atlas.reference[:, :, step]

            base64_string = convert_image_to_base64(image_array)

            if not contour:
                fig.add_trace(go.Image(visible=True, source=base64_string, hoverinfo="none",))

            else:
                fig.add_trace(go.Image(visible=True, source=base64_string))

                if view == "frontal":
                    contour = self._atlas.simplified_labels_int[step, :, :]
                elif view == "horizontal":
                    contour = self._atlas.simplified_labels_int[:, step, :]
                elif view == "sagittal":
                    contour = self._atlas.simplified_labels_int[:, :, step]

                fig.add_trace(
                    go.Contour(
                        visible=False,
                        showscale=False,
                        z=contour,
                        contours=dict(coloring="none"),
                        line_width=2,
                        line_color="gold",
                        hoverinfo="none",
                    )
                )

        # Make 1st trace visible
        fig.data[multiplier * 1].visible = True

        # Create and add slider
        steps = []
        for i in range(len(fig.data) // multiplier):
            step = dict(
                method="update",
                args=[{"visible": [False] * len(fig.data) * multiplier},],  # layout attribute
                label=subsampling[i],
            )
            step["args"][0]["visible"][multiplier * i] = True  # Toggle i'th trace to "visible"
            if contour:
                step["args"][0]["visible"][multiplier * i + 1] = True

            steps.append(step)

        sliders = [
            dict(
                active=10,
                currentvalue={"visible": False,},
                pad={"t": 30, "l": 100, "r": 100},
                steps=steps,
                # len = 0.4,
                # xanchor = 'center',
            )
        ]

        fig.update_layout(sliders=sliders)

        fig.update_layout(
            yaxis=dict(scaleanchor="x"),
            # width=1000,
            # height=800,
            title={
                "text": f"{view.capitalize()} view",
                "y": 0.99,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
                "font": dict(size=14,),
            },
            margin=dict(t=30, r=0, b=0, l=0),
        )

        fig.update_xaxes(title_text=axis_labels[1])
        fig.update_yaxes(title_text=axis_labels[0])
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)

        return fig

    def compute_root_data(self):

        # Get root data
        mesh_data_root = self._atlas.bg_atlas.mesh_from_structure("root")
        vertices_root = mesh_data_root.points
        triangles_root = mesh_data_root.cells[0].data

        # Compute points and vertices
        x_root, y_root, z_root = vertices_root.T
        I_root, J_root, K_root = triangles_root.T
        # tri_points_root = vertices_root[triangles_root]

        pl_mesh_root = go.Mesh3d(
            x=x_root / 1000 / 1000 * 25 * 10,
            y=y_root / 1000 / 1000 * 25 * 10,
            z=z_root / 1000 / 1000 * 25 * 10,
            colorscale=([0, "rgb(153, 153, 153)"], [1.0, "rgb(255,255,255)"]),
            intensity=z_root,
            flatshading=False,
            i=I_root / 1000 / 1000 * 25 * 10,
            j=J_root / 1000 / 1000 * 25 * 10,
            k=K_root / 1000 / 1000 * 25 * 10,
            opacity=0.1,
            name="Mesh CH",
            showscale=False,
        )
        return pl_mesh_root

    def compute_3D_figure(self, structure=None):

        root_lines = return_shelved_object(
            "figures/atlas_page/3D",
            "root",
            force_update=False,
            compute_function=self.compute_root_data,
        )

        layout = go.Layout(
            # title="3D atlas representation",
            font=dict(size=16, color="white"),
            scene_xaxis_visible=False,
            scene_yaxis_visible=False,
            scene_zaxis_visible=False,
            # paper_bgcolor='rgb(50,50,50)',
            margin=dict(t=10, r=10, b=10, l=10),
            # Zoom by 2 initially
            # ! Find a fix
            # scene={"aspectratio": {"x": 1, "y": 1.0, "z": 1.0}, "aspectmode": "cube"},
        )

        if structure is not None:
            # get structure data
            mesh_data = self._atlas.bg_atlas.mesh_from_structure(structure)
            vertices = mesh_data.points
            triangles = mesh_data.cells[0].data

            # compute points and vertices
            x, y, z = vertices.T
            I, J, K = triangles.T
            tri_points = vertices[triangles]

            Xe = []
            Ye = []
            Ze = []
            for T in tri_points:
                Xe.extend([T[k % 3][0] for k in range(4)] + [None])
                Ye.extend([T[k % 3][1] for k in range(4)] + [None])
                Ze.extend([T[k % 3][2] for k in range(4)] + [None])

            pl_mesh = go.Mesh3d(
                x=x,
                y=y,
                z=z,
                colorscale="Blues",
                intensity=z,
                flatshading=True,
                i=I,
                j=J,
                k=K,
                # name="Mesh CH",
                showscale=False,
            )

            pl_mesh.update(
                cmin=-7,
                lighting=dict(
                    ambient=0.2,
                    diffuse=1,
                    fresnel=0.1,
                    specular=1,
                    roughness=0.05,
                    facenormalsepsilon=1e-15,
                    vertexnormalsepsilon=1e-15,
                ),
                lightposition=dict(x=100, y=200, z=0),
            )

            # define the trace for triangle sides
            # lines = go.Scatter3d(x=Xe, y=Ye, z=Ze, mode="lines", name="", line=dict(color="rgb(70,70,70)", width=1))

        if structure is not None:
            fig = go.Figure(data=[pl_mesh, root_lines], layout=layout)
        else:
            fig = go.Figure(data=[root_lines], layout=layout)

        return fig

    def compute_3D_root_volume(self, decrease_dimensionality_factor=7):
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
            # opacityscale = "uniform",
            surface_count=2,
            colorscale="Blues",  # colorscale,
            flatshading=True,
            showscale=False,
        )

        # Return figure
        return brain_root_data

    def compute_3D_volume_figure(
        self,
        ll_t_bounds,
        name_lipid_1="",
        name_lipid_2="",
        name_lipid_3="",
        set_id_regions=None,
        decrease_dimensionality_factor=7,
    ):
        logging.info("Starting 3D volume computation")

        # Get subsampled array of annotations
        array_annotation = np.array(
            self._atlas.bg_atlas.annotation[
                ::decrease_dimensionality_factor,
                ::decrease_dimensionality_factor,
                ::decrease_dimensionality_factor,
            ],
            dtype=np.int32,
        )

        # bug correction for the last slice
        array_annotation = np.concatenate(
            (array_annotation, np.zeros((1, array_annotation.shape[1], array_annotation.shape[2])))
        )

        # Compute an array of boundaries
        array_atlas_borders = fill_array_borders(
            array_annotation, keep_structure_id=np.array(list(set_id_regions), dtype=np.int64)
        )

        logging.info("Computed basic structure array")

        # Return the lipid expression in 3D
        array_x, array_y, array_z, array_c = return_shelved_object(
            "figures/3D_page",
            "arrays_3D_" + name_lipid_1 + "_" + name_lipid_2 + "_" + name_lipid_3,
            force_update=False,
            compute_function=self.compute_array_3D,
            ignore_arguments_naming=True,
            ll_t_bounds=ll_t_bounds,
            normalize_independently=True,
            high_res=False,
        )

        logging.info("Computed array of expression in original space")
        # Compute the rescaled array of expression for each slice averaged over projected lipids
        array_slices = np.copy(array_atlas_borders)
        array_for_avg = np.full_like(array_atlas_borders, 1)
        array_x_scaled = array_x * 1000000 / self._atlas.resolution / decrease_dimensionality_factor
        array_y_scaled = array_y * 1000000 / self._atlas.resolution / decrease_dimensionality_factor
        array_z_scaled = array_z * 1000000 / self._atlas.resolution / decrease_dimensionality_factor

        @njit
        def fill_array_slices(
            array_x_scaled, array_y_scaled, array_z_scaled, array_c, array_slices, array_for_avg
        ):
            for x, y, z, c in zip(array_x_scaled, array_y_scaled, array_z_scaled, array_c):
                x_scaled = int(round(y))
                y_scaled = int(round(z))
                z_scaled = int(round(x))
                # if inside the brain but not a border
                if array_slices[x_scaled, y_scaled, z_scaled] > -0.05:
                    # if inside the brain and not assigned before
                    if abs(array_slices[x_scaled, y_scaled, z_scaled] - (-0.01)) < 10 ** -4:
                        array_slices[x_scaled, y_scaled, z_scaled] = c / 100
                    # inside the brain but already assigned, in which case average
                    else:
                        array_slices[x_scaled, y_scaled, z_scaled] += c / 100
                        array_for_avg[x_scaled, y_scaled, z_scaled] += 1

            array_slices = array_slices / array_for_avg
            return array_slices

        array_slices = fill_array_slices(
            array_x_scaled,
            array_y_scaled,
            array_z_scaled,
            np.array(array_c),
            array_slices,
            array_for_avg,
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

        if set_id_regions is not None:
            # Crop the figure to shorten interpolation time
            x_min, x_max, y_min, y_max, z_min, z_max = (
                0,
                array_annotation.shape[0],
                0,
                array_annotation.shape[1],
                0,
                array_annotation.shape[2],
            )

            # Crop unfilled parts to save space
            found = False
            for x in range(0, array_annotation.shape[0]):
                for id_structure in set_id_regions:
                    if id_structure in array_annotation[x, :, :]:
                        x_min = max(x_min, x - 1)
                        found = True
                if found:
                    break

            found = False
            for x in range(array_annotation.shape[0] - 1, -1, -1):
                for id_structure in set_id_regions:
                    if id_structure in array_annotation[x, :, :]:
                        x_max = min(x + 1, x_max)
                        found = True
                if found:
                    break

            found = False
            for y in range(0, array_annotation.shape[1]):
                for id_structure in set_id_regions:
                    if id_structure in array_annotation[:, y, :]:
                        y_min = max(y - 1, y_min)
                        found = True
                if found:
                    break

            found = False
            for y in range(array_annotation.shape[1] - 1, -1, -1):
                for id_structure in set_id_regions:
                    if id_structure in array_annotation[:, y, :]:
                        y_max = min(y + 1, y_max)
                        found = True
                if found:
                    break

            found = False
            for z in range(0, array_annotation.shape[2]):
                for id_structure in set_id_regions:
                    if id_structure in array_annotation[:, :, z]:
                        z_min = max(z - 1, z_min)
                        found = True
                if found:
                    break

            found = False
            for z in range(array_annotation.shape[2] - 1, -1, -1):
                for id_structure in set_id_regions:
                    if id_structure in array_annotation[:, :, z]:
                        z_max = min(z + 1, z_max)
                        found = True
                if found:
                    break

            if x_min is None:
                print("Bug, no voxel value has been assigned")
            else:
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
            array_annotation, array_slices, divider_radius=4
        )

        # Get root figure
        root_data = return_shelved_object(
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
                    # opacity=0.5,  # max opacity
                    opacityscale=[
                        [-0.11, 0.00],
                        [0.01, 0.0],
                        [0.5, 0.05],
                        [2.5, 0.7],
                    ],  # "uniform",
                    surface_count=10,
                    colorscale="viridis",  # "RdBu_r",
                    # flatshading=True,
                ),
                root_data,
            ]
        )

        # Hide grey background
        fig.update_layout(
            margin=dict(t=0, r=0, b=0, l=0),
            scene=dict(
                xaxis=dict(backgroundcolor="rgba(0,0,0,0)"),  # , color="grey", gridcolor="grey"),
                yaxis=dict(backgroundcolor="rgba(0,0,0,0)"),  # , color="grey", gridcolor="grey"),
                zaxis=dict(backgroundcolor="rgba(0,0,0,0)"),  # , color="grey", gridcolor="grey"),
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

                # dic_avg_lipids = {idx: [0] * n_sel for idx in set_lipids_idx}
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
        df_names = (
            self._data.get_annotations()
        )  # [self._data.get_annotations()["slice"] == slice_index]
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
        fig_heatmap_lipids = dashbio.Clustergram(
            data=df_avg_intensity_lipids.to_numpy(),
            column_labels=df_avg_intensity_lipids.columns.to_list(),
            row_labels=df_avg_intensity_lipids.index.to_list(),
            # color_threshold={
            #    'row': 250,
            #    'col': 700
            # },
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

        # set_progress(sections)
        set_progress((100, "Returning figure"))
        logging.info("Returning figure")
        return fig_heatmap_lipids

    ###### PICKLING FUNCTIONS ######
    def shelve_all_figure_3D(self, force_update=False):

        # simulate a click on all lipid names
        for name in sorted(self._data.get_annotations().name.unique()):
            structures = self._data.get_annotations()[
                self._data.get_annotations()["name"] == name
            ].structure.unique()
            for structure in sorted(structures):
                cations = self._data.get_annotations()[
                    (self._data.get_annotations()["name"] == name)
                    & (self._data.get_annotations()["structure"] == structure)
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

                    # get final lipid name
                    lipid_string = name + " " + structure + " " + cation

                    # if lipid is present in at least one slice
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

                        # compute 3D figures
                        name_lipid_1 = lipid_string
                        name_lipid_2 = ""
                        name_lipid_3 = ""

                        return_shelved_object(
                            "figures/3D_page",
                            "volume_interpolated_3D_"
                            + name_lipid_1
                            + "_"
                            + name_lipid_2
                            + "_"
                            + name_lipid_3,
                            force_update=force_update,
                            compute_function=self.compute_3D_volume_figure,
                            ignore_arguments_naming=True,
                            ll_t_bounds=lll_lipid_bounds,
                            name_lipid_1=name_lipid_1,
                            name_lipid_2=name_lipid_2,
                            name_lipid_3=name_lipid_3,
                        )
