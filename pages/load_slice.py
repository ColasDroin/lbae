# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This file contains the page used to explore the images of the MALDI acquisition in the app."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash
import numpy as np
import logging
import dash_mantine_components as dmc

# LBAE imports
from app import app, figures, storage, atlas

# ==================================================================================================
# --- Layout
# ==================================================================================================


def return_layout(basic_config, slice_index):

    page = html.Div(
        # This style is needed for keeping background color when reducing image size
        style={
            "position": "absolute",
            "top": "0px",
            "right": "0px",
            "bottom": "0px",
            "left": "6rem",
            "background-color": "#1d1c1f",
        },
        children=[
            html.Div(
                className="fixed-aspect-ratio",
                style={"background-color": "#1d1c1f"},
                children=[
                    dmc.Center(
                        style={"background-color": "#1d1c1f"},
                        children=dmc.Group(
                            class_name="mt-1",
                            children=[
                                dmc.SegmentedControl(
                                    data=[
                                        dict(label="Original slices", value="0"),
                                        dict(label="Warped slices", value="1"),
                                        dict(label="Filtered slices", value="2"),
                                        dict(label="Atlas slices", value="3"),
                                    ],
                                    id="page-1-card-tabs",
                                    value="2",
                                    radius="sm",
                                    color="cyan",
                                ),
                                dmc.Switch(
                                    id="page-1-toggle-annotations",
                                    label="Annotations",
                                    checked=False,
                                    color="cyan",
                                    radius="xl",
                                    size="sm",
                                    class_name="ml-1",
                                ),
                                dmc.Button(
                                    "Display 3D slice distribution",
                                    id="page-1-modal-button",
                                    n_clicks=0,
                                    class_name="ml-5",
                                    color="cyan",
                                ),
                            ],
                        ),
                    ),
                    dcc.Graph(
                        id="page-1-graph-slice-selection",
                        responsive=True,
                        style={
                            "width": "86%",
                            "height": "86%",
                            "position": "absolute",
                            "left": "7%",
                            "top": "7%",
                            "background-color": "#1d1c1f",
                        },
                        config=basic_config
                        | {
                            "toImageButtonOptions": {
                                "format": "png",
                                "filename": "brain_slice",
                                "scale": 2,
                            }
                        },
                        figure=storage.return_shelved_object(
                            "figures/load_page",
                            "figure_basic_image",
                            force_update=False,
                            compute_function=figures.compute_figure_basic_image,
                            type_figure="projection_corrected",
                            index_image=slice_index - 1,
                            plot_atlas_contours=False,
                        ),
                    ),
                    dmc.Text(
                        "Hovered region: ",
                        id="page-1-graph-hover-text",
                        size="lg",
                        align="center",
                        color="cyan",
                        class_name="mt-5",
                        weight=500,
                        style={
                            "width": "100%",
                            "position": "absolute",
                            "top": "7%",
                        },
                    ),
                ],
                # ),
            ),
            dbc.Modal(
                children=[
                    dbc.ModalHeader(
                        style={
                            "background-color": "#1d1c1f",
                        },
                        children=dbc.ModalTitle(
                            children="3D slice distribution",
                            style={"color": "white"},
                        ),
                    ),
                    dbc.ModalBody(
                        style={
                            "background-color": "#1d1c1f",
                        },
                        children=dbc.Spinner(
                            color="dark",
                            show_initially=False,
                            children=[
                                html.Div(
                                    children=[
                                        dcc.Graph(
                                            id="page-1-graph-modal",
                                            config=basic_config,
                                            style={
                                                "width": "100%",
                                                "height": "80vh",
                                            },
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ),
                ],
                id="page-1-modal",
                size="xl",
                is_open=False,
            ),
        ],
    )
    return page


# ==================================================================================================
# --- Callbacks
# ==================================================================================================


@app.callback(
    Output("page-1-graph-slice-selection", "figure"),
    Output("page-1-toggle-annotations", "disabled"),
    Input("main-slider", "data"),
    Input("page-1-card-tabs", "value"),
    Input("page-1-toggle-annotations", "checked"),
)
def tab_1_load_image(value_slider, active_tab, display_annotations):
    """This callback is used to update the image in page-1-graph-slice-selection from the slider."""

    # Find out which input triggered the function
    id_input, value_input = dash.callback_context.triggered[0]["prop_id"].split(".")

    if active_tab == "0":
        disabled = True
    else:
        disabled = False

    if len(id_input) > 0:

        logging.info("Slider changed to value " + str(value_slider))

        # Mapping between tab indices and type figure
        dic_mapping_tab_indices = {
            "0": "original_data",
            "1": "warped_data",
            "2": "projection_corrected",
            "3": "atlas",
        }

        # Force no annotation for the original data
        return (
            storage.return_shelved_object(
                "figures/load_page",
                "figure_basic_image",
                force_update=False,
                compute_function=figures.compute_figure_basic_image,
                type_figure=dic_mapping_tab_indices[active_tab],
                index_image=value_slider - 1,
                plot_atlas_contours=display_annotations if active_tab != "0" else False,
            ),
            disabled,
        )

    return dash.no_update


@app.callback(
    Output("page-1-graph-hover-text", "class_name"),
    Input("page-1-card-tabs", "value"),
)
def page_1_visibilty_hover(active_tab):
    """This callback is used to update the visibility of the text displayed when hovering over the
    slice image."""

    # Find out which input triggered the function
    id_input, value_input = dash.callback_context.triggered[0]["prop_id"].split(".")

    if len(id_input) > 0:
        if active_tab == "0":
            return "d-none"
        else:
            return "mt-5"
    else:
        return dash.no_update


@app.callback(
    Output("page-1-graph-hover-text", "children"),
    Input("page-1-graph-slice-selection", "hoverData"),
    State("main-slider", "data"),
)
def page_1_hover(hoverData, slice_index):
    """This callback is used to update the text displayed when hovering over the slice image."""

    # If there is a region hovered, find out the region name with the current coordinates
    if hoverData is not None:
        if len(hoverData["points"]) > 0:
            x = int(slice_index) - 1
            z = hoverData["points"][0]["x"]
            y = hoverData["points"][0]["y"]

            slice_coor_rescaled = np.asarray(
                (atlas.array_coordinates_warped_data[x, y, z] * 1000 / atlas.resolution).round(0),
                dtype=np.int16,
            )
            try:
                label = atlas.labels[tuple(slice_coor_rescaled)]
            except:
                label = "undefined"
            return "Hovered region: " + label

    return dash.no_update


@app.callback(
    Output("page-1-modal", "is_open"),
    Input("page-1-modal-button", "n_clicks"),
    State("page-1-modal", "is_open"),
)
def toggle_modal(n1, is_open):
    """This callback is used to open the modal displaying the slices in 3D."""
    if n1:
        return not is_open
    return is_open


@app.callback(
    Output("page-1-graph-modal", "figure"),
    Input("page-1-modal-button", "n_clicks"),
    Input("main-brain", "value"),
    prevent_initial_call=True,
)
def page_1_plot_graph_modal(n1, brain):
    """This callback is used to plot the figure representing the slices in 3D in the modal."""
    if n1:
        return storage.return_shelved_object(
            "figures/3D_page",
            "slices_3D",
            force_update=False,
            compute_function=figures.compute_figure_slices_3D,
            brain=brain,
        )
    return dash.no_update
