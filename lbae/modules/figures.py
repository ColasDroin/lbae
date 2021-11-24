###### IMPORT MODULES ######

# Official modules
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os
from skimage import io
import warnings

# Homemade functions
from lbae.modules.tools import spectra
from lbae.modules.tools.misc import return_pickled_object, turn_image_into_base64_string

###### DEFINE FIGURES CLASS ######
class Figures:
    __slots__ = ["_data", "_atlas"]

    def __init__(self, maldi_data, atlas):
        self._data = maldi_data
        self._atlas = atlas

    # ? Move into another class? Doesn't really need self
    def compute_padded_original_images(self):

        # Compute number of slices from the original acquisition are present in the folder
        path = "data/tiff_files/original_data/"
        n_slices = len([x for x in os.listdir(path) if "slice_" in x])
        if n_slices != self._data.get_slice_number():
            warnings.warn(
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

    def compute_figure_basic_image(self, array_image, atlas_contours=None, only_boundaries=False):

        # Create figure
        fig = go.Figure()

        # Compute image from our data if not only the atlas annotations are requested
        if not only_boundaries:

            fig.add_trace(go.Image(visible=True, source=turn_image_into_base64_string(array_image), hoverinfo="none",))

            # Add the labels only if it's not a simple annotation illustration
            fig.update_xaxes(title_text=self._atlas.bg_atlas.space.axis_labels[0][1])
            fig.update_yaxes(title_text=self._atlas.bg_atlas.space.axis_labels[0][0])

        if atlas_contours is not None:
            fig.add_trace(atlas_contours)

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

    def compute_array_figures_basic_image(self, type_figure="warped_data", plot_atlas_contours=False):

        # Either the requested figure is just a simple atlas annotation, with no background
        if type_figure == "atlas_boundaries":
            return [
                self.compute_figure_basic_image(
                    None, atlas_contours=self._atlas.list_projected_atlas_borders_figures[i], only_boundaries=True,
                )
                for i in range(self._data.get_slice_number())
            ]
        else:
            array_images = None
            if type_figure == "original_data":
                array_images = self.compute_padded_original_images()
            elif type_figure == "warped_data":
                array_images = np.array(io.imread("data/tiff_files/warped_data.tif"))
            elif type_figure == "projection":
                warnings.warn("This feature is not implemented anymore.")
                # array_images = self._atlas.array_projection
            elif type_figure == "projection_corrected":
                array_images = self._atlas.array_projection_corrected
            elif type_figure == "atlas":
                array_projected_images_atlas, array_projected_simplified_id = self._atlas.compute_array_images_atlas()
                array_images = array_projected_images_atlas

            if array_images is None:
                raise ValueError("array_images has not been assigned, can't proceed.")
            return [
                self.compute_figure_basic_image(
                    array_images[i],
                    atlas_contours=self._atlas.list_projected_atlas_borders_figures[i]
                    if plot_atlas_contours
                    else None,
                    only_boundaries=False,
                )
                for i in range(self._data.get_slice_number())
            ]

    ###### FUNCTIONS RETURNING APP GRAPHS ######
    """
    def compute_normalized_spectra(self, force_recompute=False):
        path = "data/pickled_data/normalized_spectra/"
        name_fig = "spectra_" + str(self.slice_index) + ".pickle"
        if name_fig in os.listdir(path) and not force_recompute:
            with open(path + name_fig, "rb") as atlas_file:
                return pickle.load(atlas_file)
        else:
            spectrum = compute_normalized_spectra(self.array_spectra_high_res, self.array_pixel_indexes_high_res)
            with open(path + name_fig, "wb") as atlas_file:
                pickle.dump(spectrum, atlas_file)
            return spectrum

    def return_spectrum_low_res(self, annotations=None):

        # Define figure data
        data = go.Scattergl(
            x=self.array_averaged_mz_intensity_low_res[0, :],
            y=self.array_averaged_mz_intensity_low_res[1, :],
            visible=True,
            line_color=app.dic_colors["blue"],
            fill="tozeroy",
        )
        # Define figure layout
        layout = go.Layout(
            margin=dict(t=0, r=0, b=10, l=0),
            showlegend=False,
            xaxis=dict(rangeslider={"visible": False}, title="m/z"),
            yaxis=dict(fixedrange=False, title="Intensity"),
            template="plotly_white",
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
                        fillcolor=app.dic_colors[color],
                        opacity=0.4,
                        line_color=app.dic_colors[color],
                    )
        return fig

    def return_spectrum_high_res(self, lb=None, hb=None, annotations=None, force_xlim=False, plot=True):

        # Define default values for graph (empty)
        if lb is None and hb is None:
            x = ([],)
            y = ([],)

        # If boundaries are provided, get their index
        else:
            index_lb, index_hb = return_index_boundaries(
                lb,
                hb,
                array_mz=self.array_averaged_mz_intensity_high_res[0, :],
                lookup_table=self.lookup_table_averaged_spectrum_high_res,
            )
            x = self.array_averaged_mz_intensity_high_res[0, index_lb:index_hb]
            y = self.array_averaged_mz_intensity_high_res[1, index_lb:index_hb]

        # In case download without plotting
        if not plot:
            return x, y

        # Define figure data
        data = go.Scattergl(x=x, y=y, visible=True, line_color=app.dic_colors["blue"], fill="tozeroy")

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
                        fig.add_vrect(x0=x[0], x1=x[1], line_width=0, fillcolor=app.dic_colors[color], opacity=0.4)

        # In case we don't want to zoom in too much on the selected lipid
        if force_xlim:
            fig.update_xaxes(range=[lb, hb])
        return fig

    def return_image_per_lipid(self, lb_mz, hb_mz, RGB_format=True):
        # Get image from raw mass spec data
        image = return_image_using_index_and_image_lookup(
            lb_mz,
            hb_mz,
            self.array_spectra_high_res,
            self.array_pixel_indexes_high_res,
            self.image_shape,
            self.lookup_table_spectra_high_res,
            self.cumulated_image_lookup_table_high_res,
            self.divider_lookup,
            False,
        )

        # Normalize by 99 percentile
        image = image / np.percentile(image, 99) * 1
        image = np.clip(0, 1, image)
        if RGB_format:
            image *= 255
        # image = np.round(image).astype(np.uint8) #doesn't save much memory and probably takes a little time
        return image

    def return_heatmap(
        self,
        lb_mz=None,
        hb_mz=None,
        draw=False,
        binary_string=False,
        projected_image=True,
        plot_contours=False,
        heatmap=False,
    ):
        # Upper bound lower than the lowest m/z value and higher that the highest m/z value
        if lb_mz is None:
            lb_mz = 200
        if hb_mz is None:
            hb_mz = 1800

        image = self.return_image_per_lipid(lb_mz, hb_mz, RGB_format=False)

        # project image into cleaned and higher resolution version
        if projected_image:
            image = project_image(self.slice_index, image, app.slice_atlas.array_projection_correspondence_corrected)

        # Build graph from image
        if heatmap:
            fig = px.imshow(image, binary_string=binary_string, color_continuous_scale="deep_r")  # , aspect = 'auto')
        else:
            fig = go.Figure()
            img = np.uint8(cm.viridis(image) * 255)
            pil_img = Image.fromarray(img)  # PIL image object
            prefix = "data:image/png;base64,"
            with BytesIO() as stream:
                pil_img.save(stream, format="png")  # , optimize=True, quality=85)
                base64_string = prefix + base64.b64encode(stream.getvalue()).decode("utf-8")
            fig.add_trace(go.Image(visible=True, source=base64_string))

        if plot_contours:

            fig.add_trace(app.slice_atlas.list_projected_atlas_borders_figures[self.slice_index - 1])
            # brain_regions = app.slice_atlas.array_projected_simplified_id[self.slice_index - 1, :, :]
            # contours = brain_regions[2:, 2:] - brain_regions[:-2, :-2]
            # contours = np.clip(contours ** 2, 0, 0.8)
            # contours = np.pad(contours, ((1, 1), (1, 1)))
            # contour_image = np.full(image.shape + (3,), 255, dtype=np.uint8)
            # contour_image = np.concatenate((contour_image, np.expand_dims(contours, -1)), axis=-1)

            # Build graph from image
            # fig.add_trace(go.Image(z=contour_image, colormodel="rgba", hoverinfo="skip"))

            # fig.add_trace(
            #    go.Contour(
            #        visible=True,
            #        showscale=False,
            #        z=contour,
            #        contours=dict(coloring="none"),
            #        line_width=2,
            #        line_color="gold",
            #    )
            # )

        # Improve graph layout
        fig.update_layout(
            margin=dict(t=0, r=0, b=0, l=0),
            newshape=dict(fillcolor=app.dic_colors["blue"], opacity=0.7, line=dict(color="white", width=1)),
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

    def return_heatmap_per_lipid_selection(self, ll_t_bounds, normalize_independently=True, projected_image=True):

        # Start from empty image and add selected lipids
        image = np.zeros(self.image_shape)
        for l_t_bounds in ll_t_bounds:
            if l_t_bounds is not None:
                for boundaries in l_t_bounds:
                    if boundaries is not None:
                        (l_mz, h_mz) = boundaries
                        image_temp = return_image_using_index_and_image_lookup(
                            l_mz,
                            h_mz,
                            self.array_spectra_high_res,
                            self.array_pixel_indexes_high_res,
                            self.image_shape,
                            self.lookup_table_spectra_high_res,
                            self.cumulated_image_lookup_table_high_res,
                            self.divider_lookup,
                            False,
                        )

                        if normalize_independently:
                            # image_temp = image_temp / np.max(image_temp)
                            image_temp = image_temp / np.percentile(image_temp, 99)  # * 255
                            image_temp = np.clip(0, 1, image_temp)
                        image += image_temp

        # project image into cleaned and higher resolution version
        if projected_image:
            image = project_image(self.slice_index, image, app.slice_atlas.array_projection_correspondence_corrected)

        # Build graph from image
        # fig = px.imshow(image, binary_string=False, color_continuous_scale="deep_r")

        fig = go.Figure()
        img = np.uint8(cm.viridis(image) * 255)
        pil_img = Image.fromarray(img)  # PIL image object
        prefix = "data:image/png;base64,"
        with BytesIO() as stream:
            pil_img.save(stream, format="png")  # , optimize=True, quality=85)
            base64_string_exp = prefix + base64.b64encode(stream.getvalue()).decode("utf-8")
        fig.add_trace(go.Image(visible=True, source=base64_string_exp,))

        # Improve graph layout
        fig.update_layout(
            title={
                "text": "Mass spectrometry heatmap",
                "y": 0.97,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
                "font": dict(size=14,),
            },
            margin=dict(t=30, r=0, b=10, l=0),
        )
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)
        fig.update(layout_coloraxis_showscale=False)

        return fig

    def return_rgb_array_per_lipid_selection(
        self, ll_t_bounds, normalize_independently=True, projected_image=True, log=False, enrichment=False,
    ):

        # Build a list of empty images and add selected lipids for each channel
        l_images = []
        for l_boundaries in ll_t_bounds:
            image = np.zeros(self.image_shape)
            if l_boundaries is not None:
                for boundaries in l_boundaries:
                    if boundaries is not None:
                        (l_mz, h_mz) = boundaries
                        image_temp = return_image_using_index_and_image_lookup(
                            l_mz,
                            h_mz,
                            self.array_spectra_high_res
                            if not enrichment
                            else self.return_normalized_spectra(force_recompute=False),
                            self.array_pixel_indexes_high_res,
                            self.image_shape,
                            self.lookup_table_spectra_high_res,
                            self.cumulated_image_lookup_table_high_res,
                            self.divider_lookup,
                            False,
                        )
                        if log:
                            image_temp = np.log(image_temp + 1)
                        if normalize_independently:
                            perc = np.percentile(image_temp, 99.0)
                            if perc == 0:
                                perc = np.max(image_temp)
                            if perc == 0:
                                perc = 1
                            image_temp = image_temp / perc * 255
                            image_temp = np.clip(0, 255, image_temp)

                        image += image_temp

            if not normalize_independently:
                perc = np.percentile(image, 99.0)
                if perc == 0:
                    perc = np.max(image)
                if perc == 0:
                    perc = 1
                image = image / perc * 255
                image = np.clip(0, 255, image)

            # project image into cleaned and higher resolution version
            if projected_image:
                image = project_image(
                    self.slice_index, image, app.slice_atlas.array_projection_correspondence_corrected
                )

            l_images.append(image)

        # Reoder axis to match plotly go.image requirements
        array_image = np.moveaxis(np.array(l_images), 0, 2)

        return np.asarray(array_image, dtype=np.uint8)

    def return_rgb_image_per_lipid_selection(
        self,
        ll_t_bounds,
        normalize_independently=True,
        title=True,
        projected_image=True,
        enrichment=False,
        log=False,
        return_image=False,
        use_pil=False,
    ):

        array_image = self.return_rgb_array_per_lipid_selection(
            ll_t_bounds,
            normalize_independently=normalize_independently,
            projected_image=projected_image,
            log=log,
            enrichment=enrichment,
        )

        if use_pil:
            pil_img = Image.fromarray(array_image, "RGB")  # PIL image object
            x, y = pil_img.size
            # decrease resolution to save space
            x2, y2 = int(round(x / 2)), int(round(y / 2))
            pil_img = pil_img.resize((x2, y2), Image.ANTIALIAS)
            prefix = "data:image/png;base64,"
            with BytesIO() as stream:
                pil_img.save(stream, format="png", optimize=True, quality=85)
                base64_string_exp = prefix + base64.b64encode(stream.getvalue()).decode("utf-8")
            final_image = go.Image(visible=True, source=base64_string_exp,)
        else:
            final_image = go.Image(z=array_image)

        if return_image:
            return final_image
        else:
            # Build graph from image
            fig = go.Figure(final_image)

            # Improve graph layout
            fig.update_layout(
                title={
                    "text": "Mass spectrometry heatmap" if title else "",
                    "y": 0.97,
                    "x": 0.5,
                    "xanchor": "center",
                    "yanchor": "top",
                    "font": dict(size=14,),
                },
                margin=dict(t=30, r=0, b=10, l=0),
            )
            fig.update_xaxes(showticklabels=False)
            fig.update_yaxes(showticklabels=False)

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


    @staticmethod
    def get_surface(index_slice, l_transform_parameters, array_projection, reduce_resolution_factor):

        a, u, v = l_transform_parameters[index_slice]

        ll_x = []
        ll_y = []
        ll_z = []

        for i, lambd in enumerate(range(array_projection[index_slice].shape[0])):
            l_x = []
            l_y = []
            l_z = []
            for j, mu in enumerate(range(array_projection[index_slice].shape[1])):
                x_atlas, y_atlas, z_atlas = (
                    np.array(
                        SliceAtlas.slice_to_atlas_transform(
                            a, u, v, lambd * reduce_resolution_factor, mu * reduce_resolution_factor
                        )
                    )
                    * app.slice_atlas.resolution
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
            surfacecolor=array_projection[index_slice].astype(np.int32),
            cmin=0,
            cmax=255,
            colorscale="viridis",
            opacityscale=[[0, 0], [0.1, 1], [1, 1]],
            showscale=False,
        )
        return surface

    @staticmethod
    def compute_figure_slices_3D(reduce_resolution_factor=7):

        # get transform parameters (a,u,v) for each slice
        l_transform_parameters = app.slice_atlas.return_projection_parameters()

        # reduce resolution of the slices
        new_dims = []
        n_slices = app.slice_atlas.array_coordinates_high_res.shape[0]
        d1 = app.slice_atlas.array_coordinates_high_res.shape[1]
        d2 = app.slice_atlas.array_coordinates_high_res.shape[2]
        for original_length, new_length in zip(
            app.slice_atlas.array_projection_corrected.shape,
            (n_slices, int(round(d1 / reduce_resolution_factor)), int(round(d2 / reduce_resolution_factor))),
        ):
            new_dims.append(np.linspace(0, original_length - 1, new_length))

        coords = np.meshgrid(*new_dims, indexing="ij")
        array_projection_small = map_coordinates(app.slice_atlas.array_projection_corrected, coords)

        fig = go.Figure(
            frames=[
                go.Frame(
                    data=SliceData.get_surface(
                        i, l_transform_parameters, array_projection_small, reduce_resolution_factor
                    ),
                    name=str(i + 1),
                )
                if i != 12 and i != 8
                else go.Frame(
                    data=SliceData.get_surface(
                        i - 1, l_transform_parameters, array_projection_small, reduce_resolution_factor
                    ),
                    name=str(i + 1),
                )
                for i in range(0, app.slice_atlas.n_slices, 1)
            ]
        )
        fig.add_trace(
            SliceData.get_surface(0, l_transform_parameters, array_projection_small, reduce_resolution_factor)
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
                "pad": {"b": 10, "t": 60},
                "len": 0.9,
                "x": 0.1,
                "y": 0,
                "steps": [
                    {"args": [[f.name], frame_args(0)], "label": str(k), "method": "animate",}
                    for k, f in enumerate(fig.frames)
                ],
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
            margin=dict(t=25, r=0, b=0, l=0),
            updatemenus=[
                {
                    "buttons": [
                        {"args": [None, frame_args(50)], "label": "&#9654;", "method": "animate",},  # play symbol
                        {"args": [[None], frame_args(0)], "label": "&#9724;", "method": "animate",},  # pause symbol
                    ],
                    "direction": "left",
                    "pad": {"r": 10, "t": 70},
                    "type": "buttons",
                    "x": 0.1,
                    "y": 0,
                }
            ],
            sliders=sliders,
        )

        return fig

    @staticmethod
    def return_figure_slices_3D(reduce_resolution_factor=7, force_recompute=False):
        path = "data/pickled_data/slices_3D/"
        name_fig = "slices_3D_" + str(reduce_resolution_factor) + ".pickle"
        if name_fig in os.listdir(path) and not force_recompute:
            with open(path + name_fig, "rb") as atlas_file:
                return pickle.load(atlas_file)
        else:
            fig = SliceData.compute_figure_slices_3D(reduce_resolution_factor)
            with open(path + name_fig, "wb") as atlas_file:
                pickle.dump(fig, atlas_file)
            return fig

    @staticmethod
    def compute_figure_slices_2D(ll_t_bounds, normalize_independently=True):

        fig = go.Figure(
            frames=[
                go.Frame(
                    data=app.slice_store.getSlice(i).return_rgb_image_per_lipid_selection(
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
                for i in range(1, app.slice_atlas.n_slices + 1, 1)
                if ll_t_bounds[i - 1] != [None, None, None]
            ]
        )

        fig.add_trace(
            app.slice_store.getSlice(1).return_rgb_image_per_lipid_selection(
                [
                    ll_t_bounds[i - 1]
                    for i in range(1, app.slice_atlas.n_slices + 1, 1)
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
                "pad": {"b": 10, "t": 10},
                "len": 0.9,
                "x": 0.1,
                "y": 0,
                "steps": [
                    {"args": [[f.name], frame_args(0)], "label": f.name, "method": "animate",}
                    for k, f in enumerate(fig.frames)
                ],
            }
        ]

        # Improve graph layout
        fig.update_layout(
            title={"text": "", "y": 0.97, "x": 0.5, "xanchor": "center", "yanchor": "top", "font": dict(size=14,),},
            margin=dict(t=0, r=0, b=0, l=0),
            updatemenus=[
                {
                    "buttons": [
                        {"args": [None, frame_args(50)], "label": "&#9654;", "method": "animate",},  # play symbol
                        {"args": [[None], frame_args(0)], "label": "&#9724;", "method": "animate",},  # pause symbol
                    ],
                    "direction": "left",
                    "pad": {"r": 10, "t": 10},
                    "type": "buttons",
                    "x": 0.1,
                    "y": 0,
                }
            ],
            sliders=sliders,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)

        return fig

    # This function sums over three lipids for now
    @staticmethod
    def compute_figure_bubbles_3D(ll_t_bounds, normalize_independently=True, reduce_resolution_factor=7):

        # get transform parameters (a,u,v) for each slice
        l_transform_parameters = app.slice_atlas.return_projection_parameters()
        l_x = []
        l_y = []
        l_z = []
        l_c = []
        for index_slice in range(0, app.slice_atlas.n_slices, 1):
            if ll_t_bounds[index_slice] != [None, None, None]:
                beginning = time()

                s = app.slice_store.getSlice(index_slice + 1)
                beforemiddle = time()

                array_data = s.return_rgb_array_per_lipid_selection(
                    ll_t_bounds[index_slice],
                    normalize_independently=False,
                    projected_image=False,
                    log=False,
                    enrichment=False,
                )
                middle = time()
                array_data = np.sum(array_data, axis=-1)
                array_data_stripped = array_data[array_data != 0]
                if len(array_data_stripped) > 0:
                    percentile = np.percentile(array_data_stripped, 60)
                    original_coordinates = app.slice_atlas.l_original_coor[index_slice]
                    original_coordinates_stripped = original_coordinates[array_data != 0]
                else:
                    continue

                for i in range(array_data_stripped.shape[0]):
                    # for j in range(array_data_stripped.shape[1]):
                    x_atlas, y_atlas, z_atlas = original_coordinates_stripped[i] / 1000
                    if array_data_stripped[i] >= percentile:
                        l_x.append(z_atlas)
                        l_y.append(x_atlas)
                        l_z.append(y_atlas)
                        l_c.append(array_data_stripped[i])
                end = time()
                print("loading slice took:", beforemiddle - beginning)
                print("computing pixels etc:", middle - beforemiddle)
                print("computing projection took:", end - middle)

        fig = go.Figure(
            data=go.Scatter3d(
                x=l_x,
                y=l_y,
                z=l_z,
                mode="markers",
                marker=dict(
                    sizemode="diameter",
                    sizeref=40,
                    size=l_c,
                    color=l_c,
                    colorscale="Viridis",
                    colorbar_title="Expression",
                    # line_color="rgb(140, 140, 170)",
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
            margin=dict(t=0, r=0, b=0, l=0),
            # title="Planets!",
            # scene=dict(
            #    xaxis=dict(title="Distance from Sun", titlefont_color="white"),
            #    yaxis=dict(title="Density", titlefont_color="white"),
            #    zaxis=dict(title="Gravity", titlefont_color="white"),
            #    bgcolor="rgb(20, 24, 54)",
            # ),
        )

        return fig
    """
