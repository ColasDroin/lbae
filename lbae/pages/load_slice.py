###### IMPORT MODULES ######

# Standard modules
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash
import numpy as np
import dash_draggable
import logging
import dash_mantine_components as dmc

# LBAE modules
import app
from app import figures, data
from modules.tools.misc import return_pickled_object

###### DEFFINE PAGE LAYOUT ######
# ! It seems that some things (useless?) are loaded at startup and take time
#! Put basic config in config in all page file
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
            # dmc.Center(
            #    class_name="w-100",
            #    style={"height": "100%"},
            #    children=
            html.Div(
                className="page-1-fixed-aspect-ratio",
                style={"background-color": "#1d1c1f"},
                children=[
                    dmc.Center(
                        style={"background-color": "#1d1c1f"},
                        children=dmc.Group(
                            class_name="mt-1",
                            children=[
                                # dbc.Tabs(
                                dmc.SegmentedControl(
                                    data=[
                                        dict(label="Original slices", value="0"),
                                        dict(label="Warped slices", value="1"),
                                        dict(label="Filtered slices", value="2"),
                                        dict(label="Atlas slices", value="3"),
                                    ],
                                    id="page-1-card-tabs",
                                    # card=True,
                                    # active_tab="page-1-tab-1",
                                    value="2",
                                    radius="sm",
                                    color="cyan",
                                ),
                                dmc.Button(
                                    "Display 3D slice distribution",
                                    id="page-1-modal-button",
                                    n_clicks=0,
                                    class_name="ml-5",
                                    color="cyan",
                                ),
                                dmc.Switch(
                                    id="page-1-toggle-annotations",
                                    label="Annotations",
                                    checked=False,
                                    color="cyan",
                                    radius="xl",
                                    size="sm",
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
                        # | {"staticPlot": True},
                        figure=return_pickled_object(
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
                        # className="text-warning font-weight-bold position-absolute",
                        style={
                            "width": "100%",
                            # "height": "86%",
                            "position": "absolute",
                            "top": "7%",
                        },
                    ),
                ],
                # ),
            ),
            dbc.Modal(
                # style={"background-color": "#1d1c1f",},
                children=[
                    dbc.ModalHeader(
                        style={"background-color": "#1d1c1f",},
                        children=dbc.ModalTitle(
                            children="3D slice distribution", style={"color": "white"},
                        ),
                    ),
                    dbc.ModalBody(
                        style={"background-color": "#1d1c1f",},
                        children=dbc.Spinner(
                            color="dark",
                            show_initially=False,
                            children=[
                                html.Div(
                                    className="page-1-fixed-aspect-ratio",
                                    children=[
                                        dcc.Graph(
                                            id="page-1-graph-modal",
                                            config=basic_config
                                            | {
                                                "toImageButtonOptions": {
                                                    "format": "png",
                                                    "filename": "brain_lipid_selection",
                                                    "scale": 2,
                                                }
                                            },
                                            style={
                                                "width": "100%",
                                                "height": "100%",
                                                "position": "absolute",
                                                "left": "0",
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


###### CALLBACKS ######
# Function to update the image from the slider
@app.app.callback(
    Output("page-1-graph-slice-selection", "figure"),
    Input("main-slider", "value"),
    Input("page-1-card-tabs", "value"),
    Input("page-1-toggle-annotations", "checked"),
)
def tab_1_load_image(value_slider, active_tab, display_annotations):
    logging.info("Slider changed to value " + str(value_slider))
    # Find out which input triggered the function
    id_input, value_input = dash.callback_context.triggered[0]["prop_id"].split(".")

    if len(id_input) > 0:

        # Mapping between tab indices and type figure
        dic_mapping_tab_indices = {
            "0": "original_data",
            "1": "warped_data",
            "2": "projection_corrected",
            "3": "atlas",
        }

        # Force no annotation for the original data
        return return_pickled_object(
            "figures/load_page",
            "figure_basic_image",
            force_update=False,
            compute_function=figures.compute_figure_basic_image,
            type_figure=dic_mapping_tab_indices[active_tab],
            index_image=value_slider - 1,
            plot_atlas_contours=display_annotations if active_tab != "0" else False,
        )

    return dash.no_update


@app.app.callback(
    Output("page-1-graph-hover-text", "class_name"), Input("page-1-card-tabs", "value"),
)
def page_1_visibilty_hover(active_tab):

    # Find out which input triggered the function
    id_input, value_input = dash.callback_context.triggered[0]["prop_id"].split(".")

    if len(id_input) > 0:
        if active_tab == "0":
            return "d-none"
        else:
            return "mt-5"
    else:
        return dash.no_update


@app.app.callback(
    Output("page-1-graph-hover-text", "children"),
    Input("page-1-graph-slice-selection", "hoverData"),
    State("main-slider", "value"),
)
def page_1_hover(hoverData, slice_index):
    if hoverData is not None:
        if len(hoverData["points"]) > 0:
            x = int(slice_index) - 1
            z = hoverData["points"][0]["x"]
            y = hoverData["points"][0]["y"]

            slice_coor_rescaled = np.asarray(
                (
                    app.atlas.array_coordinates_warped_data[x, y, z] * 1000 / app.atlas.resolution
                ).round(0),
                dtype=np.int16,
            )
            try:
                label = app.atlas.labels[tuple(slice_coor_rescaled)]
            except:
                label = "undefined"
            return "Hovered region: " + label

    return dash.no_update


@app.app.callback(
    Output("page-1-modal", "is_open"),
    Input("page-1-modal-button", "n_clicks"),
    State("page-1-modal", "is_open"),
)
def toggle_modal(n1, is_open):
    if n1:
        return not is_open
    return is_open


# Function to plot page-4-graph-heatmap-mz-selection when its state get updated
@app.app.callback(
    output=Output("page-1-graph-modal", "figure"),
    inputs=Input("page-1-modal-button", "n_clicks"),
    prevent_initial_call=True,
)
def page_1_plot_graph_modal(n1):
    if n1:
        return return_pickled_object(
            "figures/3D_page",
            "slices_3D",
            force_update=True,
            compute_function=figures.compute_figure_slices_3D,
        )
    return dash.no_update

