###### IMPORT MODULES ######

# Official modules
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash
import numpy as np
import dash_draggable

# App module
from lbae import app
from lbae.app import figures
from lbae import config
from lbae.modules.tools.misc import return_pickled_object

###### DEFFINE PAGE LAYOUT ######


def return_layout(basic_config, initial_slice=1):

    page = dash_draggable.ResponsiveGridLayout(
        id="draggable",
        clearSavedLayout=True,
        layouts={
            "lg": [
                {"i": "tab-1-zoom-toast", "x": 0, "y": 0, "w": 5, "h": 3},
                {"i": "tab-1modebar-toast", "x": 0, "y": 3, "w": 5, "h": 3},
                {"i": "tab-1-tooltips-toast", "x": 0, "y": 6, "w": 5, "h": 3},
                {"i": "page-1-main-toast", "x": 5, "y": 0, "w": 7, "h": 19},
            ],
            "sm": [
                {"i": "tab-1-zoom-toast", "x": 1, "y": 0, "w": 5, "h": 3},
                {"i": "tab-1modebar-toast", "x": 6, "y": 0, "w": 5, "h": 3},
                {"i": "tab-1-tooltips-toast", "x": 6, "y": 0, "w": 5, "h": 3},
                {"i": "page-1-main-toast", "x": 3, "y": 3, "w": 6, "h": 26},
            ],
        },
        children=[
            # dbc.Row(
            #    className="d-flex justify-content-center flex-wrap",
            #    justify="center",
            #    children=[
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
            # ],
            # ),
            # dbc.Row(
            #    # className="d-flex justify-content-center flex-wrap",
            #    justify="center",
            #    children=[
            #        dbc.Col(
            #            md=6,
            #            children=[
            dbc.Card(
                id="page-1-main-toast",
                style={"width": "100%", "height": "100%"},
                className="d-flex align-items-stretch",
                children=[
                    dbc.CardHeader(
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
                                className="mt-2",
                            ),
                        ],
                    ),
                    dbc.CardBody(
                        className="py-0",
                        children=[
                            ### First row
                            # dbc.Row(
                            #    justify="center",
                            #    className="d-flex align-item-center justify-content-center",
                            #    children=[
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
                                                figure=app.list_array_warped_data[initial_slice - 1],
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
                                    ### Second (nested) row
                                    # dbc.Row(
                                    #     justify="center",
                                    #     children=[
                                    #         ## First column
                                    #         dbc.Col(
                                    #             width="auto",
                                    #             children=[
                                    #                 dbc.Alert(
                                    #                     color="light",
                                    #                     style={"border-radius": "30px"},
                                    #                     className="d-flex justify-content-center",
                                    #                     children=[
                                    #                         "Please select the slice of your choice and load by clicking on the corresponding button"
                                    #                     ],
                                    #                 )
                                    #             ],
                                    #         ),
                                    #     ],
                                    # ),
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
                                                        max=len(app.list_array_warped_data),
                                                        step=None,
                                                        updatemode="drag",
                                                        marks={
                                                            x: {
                                                                "label": str(x) if x % 2 == 0 else "",
                                                                "style": {"color": config.dic_colors["dark"]},
                                                            }
                                                            for x in range(1, len(app.list_array_warped_data) + 1,)
                                                        },
                                                        value=initial_slice,
                                                    )
                                                ],
                                            ),
                                            ## Third column
                                            dbc.Col(
                                                width=2,
                                                className="mr-n1 mt-2",
                                                children=[
                                                    dbc.Button(
                                                        id="tab-1-load-button",
                                                        color="primary",
                                                        children=html.Strong("Load!"),
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                    ### Fourth (nested) row
                                    dbc.Row(
                                        justify="center",
                                        children=[
                                            dbc.Col(
                                                width=3,
                                                children=[
                                                    html.Div(
                                                        id="box-spinner",
                                                        className="mt-3",
                                                        children=[
                                                            dbc.Spinner(
                                                                color="primary",
                                                                delay_hide=1000,
                                                                children=[html.Div(id="tab-1-loading-text"),],
                                                            ),
                                                        ],
                                                    ),
                                                ],
                                            )
                                        ],
                                    ),
                                ],
                            ),
                            #    ],
                            # ),
                            html.Div("‎‎‏‏‎ ‎"),  # Empty span to prevent toast from bugging
                        ],
                    ),
                ],
            ),
            # ],
            # ),
            # ],
            # ),
        ],
    )
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
        if not display_annotations:
            if active_tab[-1] == "0":
                return app.list_array_original_data[value_slider - 1]
            if active_tab[-1] == "1":
                # return app.list_array_warped_data[value_slider - 1]

                return return_pickled_object(
                    "figures/load_page",
                    "figure_basic_images_with_slider",
                    force_update=True,
                    compute_function=figures.compute_figure_basic_images_with_slider,
                    type_figure="warped_data",
                    plot_atlas_contours=True,
                )

                return figures.compute_figure_basic_images_with_slider(plot_atlas_contours=False)
            elif active_tab[-1] == "2":
                return app.list_array_projection_corrected[value_slider - 1]
            elif active_tab[-1] == "3":
                return app.list_array_images_atlas[value_slider - 1]
        else:
            if active_tab[-1] == "0":
                return app.list_array_original_data_boundaries[value_slider - 1]
            if active_tab[-1] == "1":
                return app.list_array_warped_data_boundaries[value_slider - 1]
            elif active_tab[-1] == "2":
                return app.list_array_projection_corrected_boundaries[value_slider - 1]
            elif active_tab[-1] == "3":
                return app.list_array_images_atlas_boundaries[value_slider - 1]
    else:
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
            if (
                min(slice_coor_rescaled) >= 0
                and slice_coor_rescaled[0] < app.atlas.bg_atlas.reference.shape[0]
                and slice_coor_rescaled[1] < app.atlas.bg_atlas.reference.shape[1]
                and slice_coor_rescaled[2] < app.atlas.bg_atlas.reference.shape[2]
            ):
                label = app.atlas.labels[tuple(slice_coor_rescaled)]
            else:
                label = "undefined"
            return "Hovered region: " + label

    return dash.no_update


"""
# Function to register new slice index when load button is pressed
@app.app.callback(
    Output("tab-1-loading-text", "children"),
    Output("dcc-store-slice-index", "data"),
    Input("tab-1-load-button", "n_clicks"),
    State("page-1-slider-slice-selection", "value"),
    State("dcc-store-slice-index", "data"),
)
def tab_1_load_slice_index(clicked, value_slider, slice_index):

    # Find out which input triggered the function
    id_input, value_input = dash.callback_context.triggered[0]["prop_id"].split(".")

    # The button has been clicked
    if clicked is not None and slice_index != value_slider:

        # Cache selected slice
        app.slice_store.addSliceFromIndex(value_slider)

        # Cache correcsponding dictionnary of masks
        app.slice_atlas.return_dic_projected_masks_and_spectra(value_slider - 1)

        return None, value_slider

    # The app is initializing, button has actually not been clicked (and value_slider should be equal to initial_slice)
    else:
        # This return is needed instead of dash.no_update to activate the subsequent callbacks on dcc-store-slice-index
        if slice_index is not None:
            return None, slice_index
        else:
            return None, value_slider

"""
