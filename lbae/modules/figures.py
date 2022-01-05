###### IMPORT MODULES ######

# Official modules
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os
from skimage import io
from scipy.ndimage.interpolation import map_coordinates
import logging
from numba import njit
from matplotlib import cm

# Homemade functions
from lbae.modules.tools import spectra
from lbae.modules.tools.misc import (
    return_pickled_object,
    convert_image_to_base64,
)
from lbae.modules.tools.atlas import project_image, slice_to_atlas_transform
from lbae.modules.tools.misc import logmem
from lbae.config import dic_colors, l_colors

###### DEFINE FIGURES CLASS ######
class Figures:
    __slots__ = ["_data", "_atlas", "dic_fig_contours"]

    def __init__(self, maldi_data, atlas):
        logging.info("Initializing Figures object" + logmem())
        self._data = maldi_data
        self._atlas = atlas

        # Dic of basic contours figure (must be ultra fast because used with hovering)
        self.dic_fig_contours = return_pickled_object(
            "figures/region_analysis",
            "dic_fig_contours",
            force_update=False,
            compute_function=self.compute_dic_fig_contours,
        )

    ###### FUNCTIONS FOR FIGURE IN LOAD_SLICE PAGE ######

    # ? Move into another class? Doesn't really need self
    def compute_padded_original_images(self):

        # Compute number of slices from the original acquisition are present in the folder
        path = "lbae/data/tiff_files/original_data/"
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
    def compute_figure_basic_image(self, type_figure, index_image, plot_atlas_contours=True, only_contours=False):

        # If only boundaries is requested, force the computation of atlas contours
        if only_contours:
            plot_atlas_contours = True

        else:
            # Get array of images
            array_images = return_pickled_object(
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
                    source=convert_image_to_base64(array_image, overlay=array_image_atlas),
                    hoverinfo="none",
                )
            )

            # Add the labels only if it's not a simple annotation illustration
            fig.update_xaxes(title_text=self._atlas.bg_atlas.space.axis_labels[0][1])
            fig.update_yaxes(title_text=self._atlas.bg_atlas.space.axis_labels[0][0])

        else:
            fig.add_trace(
                go.Image(
                    visible=True,
                    source=convert_image_to_base64(
                        array_image_atlas, optimize=True, binary=True, type="RGBA", decrease_resolution_factor=8
                    ),
                    hoverinfo="none",
                )
            )

        # Improve layout
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)
        fig.update_layout(
            margin=dict(t=20, r=0, b=10, l=0),
            xaxis={"showgrid": False},
            yaxis={"showgrid": False},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        return fig

    # This function is needed to hover fast when manually selecting regions
    def compute_dic_fig_contours(self):
        dic = {}
        for slice_index in range(self._data.get_slice_number()):
            fig = return_pickled_object(
                "figures/load_page",
                "figure_basic_image",
                force_update=True,
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
            array_images = np.array(io.imread("lbae/data/tiff_files/warped_data.tif"))
        elif type_figure == "projection_corrected":
            array_images = self._atlas.array_projection_corrected
        elif type_figure == "atlas":
            array_projected_images_atlas, array_projected_simplified_id = return_pickled_object(
                "atlas/atlas_objects",
                "array_images_atlas",
                force_update=False,
                compute_function=self._atlas.compute_array_images_atlas,
            )
            array_images = array_projected_images_atlas
        return array_images

    # ? Drop this function as well? But this one works and may be kept in the future
    def compute_figure_basic_images_with_slider(self, type_figure="warped_data", plot_atlas_contours=False):
        # Get array of images
        array_images = return_pickled_object(
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
                    {"args": [[f.name], frame_args(0)], "label": f.name, "method": "animate",} for f in fig.frames
                ],
            }
        ]

        logging.info("Figure has been computed")
        return fig

    ###### FUNCTIONS FOR FIGURE IN LIPID_SELECTION PAGE ######

    def compute_image_per_lipid(
        self, slice_index, lb_mz, hb_mz, RGB_format=True, normalize=True, log=False, projected_image=True
    ):
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
        )

        if log:
            image = np.log(image + 1)

        if normalize:
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
            image = project_image(slice_index, image, self._atlas.array_projection_correspondence_corrected)
        return image

    # ! Check in the end if this function is redundant with return_heatmap_per_lipid_selection
    def compute_heatmap_per_mz(
        self,
        slice_index,
        lb_mz=None,
        hb_mz=None,
        draw=False,
        binary_string=False,
        projected_image=True,
        plot_contours=False,
        heatmap=False,
    ):
        if binary_string:
            logging.info("binary_string is set to True, therefore the plot will be made as a heatmap")
            heatmap = True

        # Upper bound lower than the lowest m/z value and higher that the highest m/z value
        if lb_mz is None:
            lb_mz = 200
        if hb_mz is None:
            hb_mz = 1800

        # Compute image with largest possible bounds
        image = self.compute_image_per_lipid(
            slice_index, lb_mz, hb_mz, RGB_format=True, projected_image=projected_image
        )

        # Clean memmap memory
        self._data.clean_memory(slice_index=slice_index)

        # Build graph from image
        # ! Do I want to keep the heatmap option? I think not as it's slower
        if heatmap:
            fig = px.imshow(image, binary_string=binary_string, color_continuous_scale="deep_r")  # , aspect = 'auto')
            if plot_contours:
                logging.warning("Contour plot is not compatible with heatmap plot for now.")
                # Compute it anyway but won't work
                b64_string = convert_image_to_base64(
                    self._atlas.list_projected_atlas_borders_arrays[slice_index - 1], type="RGBA"
                )
                fig.add_trace(go.Image(visible=True, source=b64_string))

        else:
            fig = go.Figure()

            if plot_contours:
                array_image_atlas = self._atlas.list_projected_atlas_borders_arrays[slice_index - 1]
            else:
                array_image_atlas = None

            base64_string = convert_image_to_base64(image, overlay=array_image_atlas)
            fig.add_trace(go.Image(visible=True, source=base64_string))

        # Improve graph layout
        fig.update_layout(
            margin=dict(t=0, r=0, b=0, l=0),
            newshape=dict(fillcolor=dic_colors["blue"], opacity=0.7, line=dict(color="white", width=1)),
            # Do not specify height for now as plotly is buggued and resets it to 450px if switching tabs
            # height=500,
        )
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)
        fig.update(layout_coloraxis_showscale=False)

        # Set how the image should be annotated
        if draw:
            fig.update_layout(dragmode="drawclosedpath")

        return fig

    def compute_heatmap_per_lipid_selection(
        self, slice_index, ll_t_bounds, normalize_independently=True, projected_image=True
    ):

        # Start from empty image and add selected lipids
        image = np.zeros(self._atlas.image_shape)
        for l_t_bounds in ll_t_bounds:
            if l_t_bounds is not None:
                for boundaries in l_t_bounds:
                    if boundaries is not None:
                        (lb_mz, hb_mz) = boundaries
                        image_temp = self.compute_image_per_lipid(
                            slice_index,
                            lb_mz,
                            hb_mz,
                            RGB_format=True,
                            normalize=normalize_independently,
                            projected_image=projected_image,
                        )

                        image += image_temp

        # Clean memmap memory
        self._data.clean_memory(slice_index=slice_index)

        # Build figure
        fig = go.Figure()
        base64_string = convert_image_to_base64(image)
        fig.add_trace(go.Image(visible=True, source=base64_string))

        # Improve graph layout
        fig.update_layout(
            #     title={
            #         "text": "Mass spectrometry heatmap",
            #         "y": 0.97,
            #         "x": 0.5,
            #         "xanchor": "center",
            #         "yanchor": "top",
            #         "font": dict(size=14,),
            #     },
            margin=dict(t=10, r=0, b=10, l=0),
        )
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)
        fig.update(layout_coloraxis_showscale=False)

        return fig

    def compute_rgb_array_per_lipid_selection(
        self,
        slice_index,
        ll_t_bounds,
        normalize_independently=True,
        projected_image=True,
        log=False,
        enrichment=False,
    ):

        # Build a list of empty images and add selected lipids for each channel
        l_images = []
        for l_boundaries in ll_t_bounds:
            image = np.zeros(self._atlas.image_shape if projected_image else self._data.get_image_shape(slice_index))
            if l_boundaries is not None:
                for boundaries in l_boundaries:
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
        title=True,
        projected_image=True,
        enrichment=False,
        log=False,
        return_image=False,
        use_pil=True,
    ):
        logging.info("Started RGB image computation for slice " + str(slice_index) + logmem())

        # Get RGB array for the current lipid selection
        array_image = self.compute_rgb_array_per_lipid_selection(
            slice_index,
            ll_t_bounds,
            normalize_independently=normalize_independently,
            projected_image=projected_image,
            log=log,
            enrichment=enrichment,
        )
        logging.info("array_image acquired for slice " + str(slice_index) + logmem())

        if use_pil:
            base64_string_exp = convert_image_to_base64(array_image, type="RGB")
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
                # title={
                #    "text": "Mass spectrometry heatmap" if title else "",
                #    "y": 0.97,
                #    "x": 0.5,
                #    "xanchor": "center",
                #    "yanchor": "top",
                #    "font": dict(size=14,),
                # },
                margin=dict(t=10, r=0, b=10, l=0),
            )
            fig.update_xaxes(showticklabels=False)
            fig.update_yaxes(showticklabels=False)
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
            margin=dict(t=0, r=0, b=10, l=0),
            showlegend=False,
            xaxis=dict(rangeslider={"visible": False}, title="m/z"),
            yaxis=dict(fixedrange=False, title="Intensity"),
            template="plotly_white",
            autosize=True,
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

    def compute_spectrum_high_res(self, slice_index, lb=None, hb=None, annotations=None, force_xlim=False, plot=True):

        # Define default values for graph (empty)
        if lb is None and hb is None:
            x = ([],)
            y = ([],)

        # If boundaries are provided, get their index
        else:
            index_lb, index_hb = spectra.compute_index_boundaries(
                lb,
                hb,
                array_spectra_avg=self._data.get_array_avg_spectrum(slice_index),
                lookup_table=self._data.get_array_lookup_mz_avg(slice_index),
            )
            x = self._data.get_array_avg_spectrum(slice_index)[0, index_lb:index_hb]
            y = self._data.get_array_avg_spectrum(slice_index)[1, index_lb:index_hb]

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
            template="plotly_white",
            title={
                "text": "High resolution spectrum (averaged across pixels)",
                "y": 0.92,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
                "font": dict(size=14,),
            },
        )
        # Build figure layout
        fig = go.Figure(data=data, layout=layout)

        # Annotate selected lipids with vertical bars
        if annotations is not None:
            for color, x in zip(["red", "green", "blue"], annotations):
                if x is not None:
                    if x[0] >= lb and x[-1] <= hb:
                        fig.add_vrect(x0=x[0], x1=x[1], line_width=0, fillcolor=dic_colors[color], opacity=0.4)

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
            template="plotly_white",
        )
        # Build figure
        fig = go.Figure(data=data, layout=layout)
        return fig

    def return_heatmap_lipid(self, fig=None):

        # Build empty figure if not provided
        if fig is None:
            fig = go.Figure(data=go.Heatmap(z=[[]], x=[], y=[], visible=True))

        # Improve figure layout
        fig.update_layout(
            margin=dict(t=25, r=0, b=10, l=0), template="plotly_white", font_size=8,
        )
        return fig

    def compute_figure_slices_3D(self, reduce_resolution_factor=7):

        # get transform parameters (a,u,v) for each slice
        l_transform_parameters = return_pickled_object(
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
            (n_slices, int(round(d1 / reduce_resolution_factor)), int(round(d2 / reduce_resolution_factor))),
        ):
            new_dims.append(np.linspace(0, original_length - 1, new_length))

        coords = np.meshgrid(*new_dims, indexing="ij")
        array_projection_small = map_coordinates(self._atlas.array_projection_corrected, coords)

        fig = go.Figure(
            frames=[
                go.Frame(
                    data=self.get_surface(i, l_transform_parameters, array_projection_small, reduce_resolution_factor),
                    name=str(i + 1),
                )
                if i != 12 and i != 8
                else go.Frame(
                    data=self.get_surface(
                        i - 1, l_transform_parameters, array_projection_small, reduce_resolution_factor
                    ),
                    name=str(i + 1),
                )
                for i in range(0, self._data.get_slice_number(), 1)
            ]
        )
        fig.add_trace(self.get_surface(0, l_transform_parameters, array_projection_small, reduce_resolution_factor))

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
                    range=[0.05 / 7 * reduce_resolution_factor, 0.33 / 7 * reduce_resolution_factor], autorange=False
                ),
                zaxis=dict(
                    range=[0.2 / 7 * reduce_resolution_factor, -0.02 / 7 * reduce_resolution_factor], autorange=False
                ),
                xaxis=dict(
                    range=[0.0 / 7 * reduce_resolution_factor, 0.28 / 7 * reduce_resolution_factor], autorange=False
                ),
            ),
            margin=dict(t=5, r=0, b=0, l=0),
            # updatemenus=[
            #     {
            #         "buttons": [
            #             {"args": [None, frame_args(50)], "label": "&#9654;", "method": "animate",},  # play symbol
            #             {"args": [[None], frame_args(0)], "label": "&#9724;", "method": "animate",},  # pause symbol
            #         ],
            #         "direction": "left",
            #         "pad": {"r": 10, "t": 70},
            #         "type": "buttons",
            #         "x": 0.1,
            #         "y": 0,
            #     }
            # ],
            sliders=sliders,
        )

        return fig

    # ! I can probably numbaize that
    def get_surface(self, slice_index, l_transform_parameters, array_projection, reduce_resolution_factor):

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
            title={"text": "", "y": 0.97, "x": 0.5, "xanchor": "center", "yanchor": "top", "font": dict(size=14,),},
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

    # This function sums over the selected lipids for now
    def compute_figure_bubbles_3D(self, ll_t_bounds, normalize_independently=True, reduce_resolution_factor=7):

        logging.info("Starting computing 3D figure" + logmem())
        # get transform parameters (a,u,v) for each slice
        l_transform_parameters = return_pickled_object(
            "atlas/atlas_objects",
            "l_transform_parameters",
            force_update=False,
            compute_function=self._atlas.compute_projection_parameters,
        )

        # get list of original coordinates foe each slice
        l_original_coor = self._atlas.l_original_coor

        # Initialize empty arrays with a large estimate of 400*400 for the orginal acquisition size
        max_size = 400 * 400 * self._data.get_slice_number()
        array_x = np.empty(max_size, dtype=np.float32)
        array_y = np.empty(max_size, dtype=np.float32)
        array_z = np.empty(max_size, dtype=np.float32)
        array_c = np.empty(max_size, dtype=np.int16)
        total_index = 0
        logging.debug(f"Size array_x: {array_x.nbytes / 1024 / 1024 :.2f}")
        logging.info("Starting slice iteration" + logmem())

        # Define a numba function to accelerate the loop in which the ccfv3 coordinates are computed and the final
        # arrays are filled
        @njit
        def return_final_array(
            array_data_stripped,
            original_coordinates_stripped,
            percentile,
            array_x,
            array_y,
            array_z,
            array_c,
            total_index,
        ):
            # Keep track of the array indexing even outside of this function
            total_index_temp = 0
            for i in range(array_data_stripped.shape[0]):
                x_atlas, y_atlas, z_atlas = original_coordinates_stripped[i] / 1000
                if array_data_stripped[i] >= percentile:
                    array_x[total_index + total_index_temp] = z_atlas
                    array_y[total_index + total_index_temp] = x_atlas
                    array_z[total_index + total_index_temp] = y_atlas
                    array_c[total_index + total_index_temp] = array_data_stripped[i]
                    total_index_temp += 1

            total_index += total_index_temp
            return array_x, array_y, array_z, array_c, total_index

        for slice_index in range(0, self._data.get_slice_number(), 1):
            if ll_t_bounds[slice_index] != [None, None, None]:

                # Get the data as an expression image per lipid
                array_data = self.compute_rgb_array_per_lipid_selection(
                    slice_index + 1,
                    ll_t_bounds[slice_index],
                    normalize_independently=True,
                    projected_image=False,
                    log=False,
                    enrichment=False,
                )

                # Sum array colors (i.e. lipids)
                array_data = np.sum(array_data, axis=-1)

                # Remove pixels for which lipid expression is zero
                array_data_stripped = array_data[array_data != 0]

                # Skip the current slice if expression is very sparse
                if len(array_data_stripped) < 10:
                    continue

                # Compute the percentile of expression to filter out lowly expressed pixels
                percentile = np.percentile(array_data_stripped, 60)

                # Get the coordinates of the pixels in the ccfv3
                original_coordinates = l_original_coor[slice_index]
                original_coordinates_stripped = original_coordinates[array_data != 0]

                array_x, array_y, array_z, array_c, total_index = return_final_array(
                    array_data_stripped,
                    original_coordinates_stripped,
                    percentile,
                    array_x,
                    array_y,
                    array_z,
                    array_c,
                    total_index,
                )
                logging.info("Slice " + str(slice_index) + " done" + logmem())

        # Strip the arrays from the zeros
        array_x = array_x[:total_index]
        array_y = array_y[:total_index]
        array_z = array_z[:total_index]
        array_c = array_c[:total_index].tolist()

        # Reopen all memaps
        fig = go.Figure(
            data=go.Scatter3d(
                x=array_x,
                y=array_y,
                z=array_z,
                mode="markers",
                marker=dict(
                    # sizemode="diameter",
                    # sizeref=40,
                    size=3,  # array_c,
                    color=array_c,
                    colorscale="Viridis",
                    colorbar_title="Expression",
                    # line_color="rgba(140, 140, 170, 0.01)",
                ),
            )
        )
        fig.update_layout(
            scene=dict(
                # zaxis=dict(autorange=False),
                # aspectratio=dict(x=1.5, y=1, z=1),
                # zaxis_autorange="reversed",
                # aspectmode = "data",
                # yaxis=dict(
                #    range=[0.0 / 7 * reduce_resolution_factor, 0.33 / 7 * reduce_resolution_factor], autorange=False
                # ),
                # zaxis=dict(
                #    range=[0.3 / 7 * reduce_resolution_factor, -0.02 / 7 * reduce_resolution_factor], autorange=False
                # ),
                # xaxis=dict(
                #    range=[0.0 / 7 * reduce_resolution_factor, 0.28 / 7 * reduce_resolution_factor], autorange=False
                # ),
            ),
            margin=dict(t=5, r=0, b=0, l=0),
            # title="Planets!",
            # scene=dict(
            #    xaxis=dict(title="Distance from Sun", titlefont_color="white"),
            #    yaxis=dict(title="Density", titlefont_color="white"),
            #    zaxis=dict(title="Gravity", titlefont_color="white"),
            #    bgcolor="rgb(20, 24, 54)",
            # ),
        )
        logging.info("Done" + logmem())
        return fig

    def compute_sunburst_figure(self, maxdepth=3):
        fig = px.sunburst(names=self._atlas.l_nodes, parents=self._atlas.l_parents, maxdepth=maxdepth)
        fig.update_layout(margin=dict(t=0, r=0, b=0, l=0),)
        return fig

    def compute_atlas_with_slider(self, view="frontal", contour=False):
        # Check that the given view exists
        if view not in ("frontal", "horizontal", "sagittal"):
            print(
                "The provided view must be of of the following: frontal, horizontal, or sagittal. Back to default, i.e. frontal"
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

        subsampling = list(range(0, self._atlas.bg_atlas.reference.shape[idx_view], self._atlas.subsampling_block))
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
                pad={"t": 10, "l": 100, "r": 100},
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
            margin=dict(t=5, r=0, b=0, l=0),
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
            x=x_root,
            y=y_root,
            z=z_root,
            colorscale=([0, "rgb(153, 153, 153)"], [1.0, "rgb(255,255,255)"]),
            intensity=z_root,
            flatshading=False,
            i=I_root,
            j=J_root,
            k=K_root,
            opacity=0.1,
            name="Mesh CH",
            showscale=False,
        )
        return pl_mesh_root

    def compute_3D_figure(self, structure=None):

        root_lines = return_pickled_object(
            "figures/atlas_page/3D", "root", force_update=False, compute_function=self.compute_root_data
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

    """

 



   
  

    # This function averages spectra from a drawn selection and pads the remaining peaks with zeros
    def compute_extended_spectrum_per_selection(self, path, debug=False, sample=False, zero_extend=True):
        list_index_bound_rows, list_index_bound_column_per_row = sample_rows_from_path(path)
        l_mz_intensities = compute_spectrum_per_row_selection(
            list_index_bound_rows,
            list_index_bound_column_per_row,
            self.array_spectra_high_res,
            self.array_pixel_indexes_high_res,
            self.image_shape,
            zeros_extend=zero_extend,
            sample=sample,
        )
        if debug:
            return list_index_bound_rows, list_index_bound_column_per_row, l_mz_intensities
        else:
            return l_mz_intensities
   

    """
