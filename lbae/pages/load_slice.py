###### IMPORT MODULES ######

# Official modules
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash
import numpy as np
import dash_draggable
import dash_mantine_components as dmc

# Homemade modules
from lbae import app
from lbae.app import figures, data
from lbae import config
from lbae.modules.tools.misc import return_pickled_object

###### DEFFINE PAGE LAYOUT ######

#! Put basic config in config in all page file
def return_layout(basic_config, initial_slice=1):

    page = [
        dmc.NotificationsProvider(dmc.NotificationHandler(id="notif-zoom",), autoClose=False,),
        dmc.NotificationsProvider(dmc.NotificationHandler(id="notif-modebar",), autoClose=False,),
        dash_draggable.ResponsiveGridLayout(
            id="draggable",
            clearSavedLayout=True,
            isDraggable=False,
            isResizable=False,
            layouts={
                "lg": [
                    {"i": "tab-1-zoom-toast", "x": 0, "y": 0, "w": 5, "h": 3},
                    {"i": "tab-1modebar-toast", "x": 0, "y": 3, "w": 5, "h": 3},
                    {"i": "tab-1-tooltips-toast", "x": 0, "y": 6, "w": 5, "h": 3},
                    {"i": "page-1-main-toast", "x": 5, "y": 0, "w": 7, "h": 20},
                ],
                "sm": [
                    {"i": "tab-1-zoom-toast", "x": 1, "y": 0, "w": 5, "h": 3},
                    {"i": "tab-1modebar-toast", "x": 6, "y": 0, "w": 5, "h": 3},
                    {"i": "tab-1-tooltips-toast", "x": 6, "y": 0, "w": 5, "h": 3},
                    {"i": "page-1-main-toast", "x": 3, "y": 3, "w": 6, "h": 26},
                ],
            },
            children=[
                # Toast to explain how zoom works
                dbc.Toast(
                    """On any graph (heatmap or m/z plot), you can draw a square with your mouse to zoom in, 
        and double click to reset zoom level.""",
                    id="tab-1-zoom-toast",
                    header="How to use zoom",
                    # header_style={"background-color": "#3a8bb6"},
                    is_open=True,
                    dismissable=False,
                    style={"width": "100%", "height": "100%",}
                    # className="mx-3 mb-3 mt-1",
                    # style={"position": "fixed", "top": 5, "left": 80 + 10, "width": 350},
                ),
                # Toast to explain modebard
                dbc.Toast(
                    """You can interact more with the figures (zoom, pan, reset axes, download) 
        using the modebard above them.""",
                    id="tab-1modebar-toast",
                    header="Using the modebard",
                    # header_style={"background-color": "#3a8bb6"},
                    is_open=True,
                    dismissable=False,
                    style={"width": "100%", "height": "100%",}
                    # className="mx-3 mb-3 mt-1",
                    # style={"position": "fixed", "top": 5, "left": 80 + 400, "width": 350},
                ),
                # Toast to remind user of tooltips
                dbc.Toast(
                    """Most of the items in the app are embedded with advice.
            Just position your mouse over an item to get a tip on how to use it.""",
                    id="tab-1-tooltips-toast",
                    header="Tooltips",
                    # header_style={"background-color": "#3a8bb6"},
                    is_open=True,
                    dismissable=False,
                    style={"width": "100%", "height": "100%",}
                    # className="mx-3 mb-3 mt-1",
                    # style={"position": "fixed", "top": 5, "left": 80 + 790, "width": 350},
                ),
                dbc.Card(
                    id="page-1-main-toast",
                    style={"width": "100%", "height": "100%"},
                    className="d-flex align-items-stretch",
                    children=[
                        dbc.CardHeader(
                            className="d-flex align-items-stretch",
                            children=[
                                dbc.Tabs(
                                    [
                                        dbc.Tab(label="Original slices", tab_id="page-1-tab-0"),
                                        dbc.Tab(label="Warped slices", tab_id="page-1-tab-1"),
                                        dbc.Tab(label="Corrected projected slices", tab_id="page-1-tab-2"),
                                        dbc.Tab(label="Atlas slices", tab_id="page-1-tab-3"),
                                    ],
                                    id="page-1-card-tabs",
                                    # card=True,
                                    active_tab="page-1-tab-1",
                                    # className="mr-5 pr-5",
                                ),
                                dbc.Switch(
                                    id="page-1-toggle-annotations",
                                    label="Display annotations",
                                    value=False,
                                    className="ml-5 mt-2",
                                ),
                            ],
                        ),
                        dbc.CardBody(
                            className="py-0 ",
                            children=[
                                ## First column
                                dbc.Col(
                                    width=12,
                                    children=[
                                        html.Div(
                                            className="loading-wrapper page-1-fixed-aspect-ratio",
                                            children=[
                                                # dbc.Spinner(
                                                #    color="dark",
                                                # spinner_style={"margin": "auto"},
                                                #    children=[
                                                dcc.Graph(
                                                    id="page-1-graph-slice-selection",
                                                    responsive=True,
                                                    style={
                                                        "width": "100%",
                                                        "height": "100%",
                                                        "position": "absolute",
                                                        "left": "0",
                                                    },
                                                    config=basic_config
                                                    | {
                                                        "toImageButtonOptions": {
                                                            "format": "png",
                                                            "filename": "brain_slice",
                                                            "scale": 2,
                                                        }
                                                    },
                                                    figure=return_pickled_object(
                                                        "figures/load_page",
                                                        "figure_basic_image",
                                                        force_update=False,
                                                        compute_function=figures.compute_figure_basic_image,
                                                        type_figure="warped_data",
                                                        index_image=0,
                                                        plot_atlas_contours=False,
                                                    ),
                                                ),
                                                html.P(
                                                    "Hovered region: ",
                                                    id="page-1-graph-hover-text",
                                                    className="text-warning font-weight-bold position-absolute",
                                                    style={"left": "10%", "top": "2em"},
                                                ),
                                                # ],
                                                # )
                                            ],
                                        ),
                                        ### Third (nested) row
                                        dbc.Row(
                                            justify="center",
                                            children=[
                                                # Empty column for centering
                                                # dbc.Col(width = 1),
                                                ## First column
                                                dbc.Col(
                                                    width=1,
                                                    className="px-0 mt-4 mr-1 text-right",
                                                    children=[html.P("Slice: ")],
                                                ),
                                                ## Second column
                                                dbc.Col(
                                                    width=9,
                                                    className="mt-3",
                                                    children=[
                                                        dcc.Slider(
                                                            className="px-0 mx-0",
                                                            id="page-1-slider-slice-selection",
                                                            min=1,
                                                            max=data.get_slice_number(),
                                                            step=None,
                                                            updatemode="drag",
                                                            marks={
                                                                x: {
                                                                    "label": str(x) if x % 2 == 0 else "",
                                                                    "style": {"color": config.dic_colors["dark"]},
                                                                }
                                                                for x in range(1, data.get_slice_number() + 1,)
                                                            },
                                                            value=initial_slice,
                                                        )
                                                    ],
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                #    ],
                                # ),
                                html.Div(""),  # Empty span to prevent toast from bugging
                            ],
                        ),
                    ],
                ),
                # ],
                # ),
                # ],
                # ),
            ],
        ),
    ]
    return page


###### CALLBACKS ######
# Function to update the image from the slider
@app.app.callback(
    Output("page-1-graph-slice-selection", "figure"),
    Input("page-1-slider-slice-selection", "value"),
    Input("page-1-card-tabs", "active_tab"),
    Input("page-1-toggle-annotations", "value"),
)
def tab_1_load_image(value_slider, active_tab, display_annotations):

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
            type_figure=dic_mapping_tab_indices[active_tab[-1]],
            index_image=value_slider - 1,
            plot_atlas_contours=display_annotations if active_tab[-1] != "0" else False,
        )

    return dash.no_update


@app.app.callback(
    Output("page-1-graph-hover-text", "className"), Input("page-1-card-tabs", "active_tab"),
)
def page_1_visibilty_hover(active_tab):

    # Find out which input triggered the function
    id_input, value_input = dash.callback_context.triggered[0]["prop_id"].split(".")

    if len(id_input) > 0:
        if active_tab[-1] == "0":
            return "d-none"
        else:
            return "text-warning font-weight-bold position-absolute"
    else:
        return dash.no_update


@app.app.callback(
    Output("page-1-graph-hover-text", "children"),
    Input("page-1-graph-slice-selection", "hoverData"),
    State("page-1-slider-slice-selection", "value"),
)
def page_1_hover(hoverData, slice_index):
    if hoverData is not None:
        if len(hoverData["points"]) > 0:
            x = int(slice_index) - 1
            z = hoverData["points"][0]["x"]
            y = hoverData["points"][0]["y"]

            slice_coor_rescaled = np.asarray(
                (app.atlas.array_coordinates_warped_data[x, y, z] * 1000 / app.atlas.resolution).round(0),
                dtype=np.int16,
            )
            try:
                label = app.atlas.labels[tuple(slice_coor_rescaled)]
            except:
                label = "undefined"
            return "Hovered region: " + label

    return dash.no_update


@app.app.callback(
    Output("notif-zoom", "task"), Input("session-id", "data"), prevent_initial_call=False,
)
def notif_zoom(test):

    task = {
        "command": "show",
        "id": "notification",
        "props": {
            "color": "violet",
            "title": "How to use zoom",
            "message": "On any graph (heatmap or m/z plot), you can draw a square with your mouse to zoom in, and double click to reset zoom level.",
            "loading": False,
            "disallowClose": False,
        },
    }

    return task


@app.app.callback(
    Output("notif-modebar", "task"), Input("notif-zoom", "task"), prevent_initial_call=False,
)
def notif_modebar(test):

    task = {
        "command": "show",
        "id": "notification",
        "props": {
            "color": "violet",
            "title": "Modebar",
            "message": "On any graph (heatmap or m/z plot), you can draw a square with your mouse to zoom in, and double click to reset zoom level.",
            "loading": False,
            "disallowClose": False,
        },
    }

    return task

