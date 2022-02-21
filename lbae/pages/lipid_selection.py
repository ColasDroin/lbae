###### IMPORT MODULES ######

# Standard modules
import dash_bootstrap_components as dbc
from dash import dcc, html
import logging
import dash
import json
import pandas as pd
from dash.dependencies import Input, Output, State, ALL
import dash_draggable
import numpy as np
import dash_mantine_components as dmc

# LBAE modules
from app import figures, data
import app
from modules.tools.misc import return_pickled_object

HEIGHT_PLOTS = 280
N_LINES = int(np.ceil(HEIGHT_PLOTS / 30))

###### DEFFINE PAGE LAYOUT ######


def return_layout(basic_config, slice_index):

    page = (
        # dash_draggable.ResponsiveGridLayout(
        #     id="draggable",
        #     clearSavedLayout=True,
        #     isDraggable=False,
        #     isResizable=False,
        #     containerPadding=[2, 2],
        #     breakpoints={"xxl": 1600, "lg": 1200, "md": 996, "sm": 768, "xs": 480, "xxs": 0},
        #     gridCols={"xxl": 12, "lg": 12, "md": 10, "sm": 6, "xs": 4, "xxs": 2},
        #     layouts={
        #         # x sets the lateral position, y the vertical one, w is in columns (whose size depends on the dimension), h is in rows (30px)
        #         # nb columns go 12->10->6->4->2
        #         "xxl": [
        #             {"i": "page-2-card-heatmap", "x": 0, "y": 0, "w": 12, "h": 29},
        #             {"i": "page-2-card-low-res", "x": 7, "y": 0, "w": 5, "h": N_LINES},
        #             {"i": "page-2-card-high-res", "x": 7, "y": 20, "w": 5, "h": N_LINES},
        #         ],
        #         "lg": [
        #             {"i": "page-2-card-heatmap", "x": 0, "y": 0, "w": 7, "h": 16},
        #             {"i": "page-2-card-low-res", "x": 7, "y": 16, "w": 5, "h": N_LINES},
        #             {"i": "page-2-card-high-res", "x": 7, "y": 16, "w": 5, "h": N_LINES},
        #         ],
        #         "md": [
        #             {"i": "page-2-card-heatmap", "x": 0, "y": 0, "w": 6, "h": 14},
        #             {"i": "page-2-card-low-res", "x": 0, "y": 14, "w": 5, "h": N_LINES},
        #             {"i": "page-2-card-high-res", "x": 5, "y": 14, "w": 5, "h": N_LINES},
        #         ],
        #         "sm": [
        #             {"i": "page-2-card-heatmap", "x": 0, "y": 0, "w": 6, "h": 19},
        #             {"i": "page-2-card-low-res", "x": 0, "y": 19 + 7 + 5, "w": 6, "h": N_LINES},
        #             {
        #                 "i": "page-2-card-high-res",
        #                 "x": 0,
        #                 "y": 19 + 7 + 5 + N_LINES,
        #                 "w": 6,
        #                 "h": N_LINES,
        #             },
        #         ],
        #         "xs": [
        #             {"i": "page-2-card-heatmap", "x": 0, "y": 0, "w": 4, "h": 14},
        #             {"i": "page-2-card-low-res", "x": 0, "y": 14 + 7 + 5, "w": 4, "h": N_LINES},
        #             {
        #                 "i": "page-2-card-high-res",
        #                 "x": 0,
        #                 "y": 14 + 7 + 5 + N_LINES,
        #                 "w": 4,
        #                 "h": N_LINES,
        #             },
        #         ],
        #         "xxs": [
        #             {"i": "page-2-card-heatmap", "x": 0, "y": 0, "w": 2, "h": 9},
        #             {"i": "page-2-card-low-res", "x": 0, "y": 9 + 7 + 5, "w": 2, "h": N_LINES},
        #             {
        #                 "i": "page-2-card-high-res",
        #                 "x": 0,
        #                 "y": 9 + 7 + 5 + N_LINES,
        #                 "w": 2,
        #                 "h": N_LINES,
        #             },
        #         ],
        #     },
        html.Div(
            style={
                "position": "absolute",
                "top": "0px",
                "right": "0px",
                "bottom": "0px",
                "left": "5.5rem",
                "background-color": "#1d1c1f",
            },
            children=[
                # dbc.Card(
                #     id="page-2-card-heatmap",
                #     className="no-transition",
                #     style={"width": "100%", "height": "100%"},
                #     children=[
                #         dbc.CardHeader(
                #             id="page-2-toast-graph-heatmap-mz-selection",
                #             className="d-flex",
                #             children=[html.Div("Brain slice n°"),],
                #         ),
                #         dbc.CardBody(
                #             className="py-0 mb-0 mt-2",
                #             children=[
                #                 dbc.Spinner(
                #                     color="dark",
                #                     show_initially=False,
                #                     children=[
                # dmc.Paper(
                #     id="page-2-card-heatmap",
                #     children=[
                dmc.Center(
                    class_name="w-100",
                    style={"height": "90%"},  # Boostrap doesn't support h-90...
                    children=html.Div(
                        className="page-1-fixed-aspect-ratio",
                        style={"background-color": "#1d1c1f"},
                        children=[
                            dcc.Graph(
                                id="page-2-graph-heatmap-mz-selection",
                                config=basic_config
                                | {
                                    "toImageButtonOptions": {
                                        "format": "png",
                                        "filename": "brain_lipid_selection",
                                        "scale": 2,
                                    }
                                }
                                | {"staticPlot": False},
                                style={
                                    "width": "100%",
                                    "height": "100%",
                                    "position": "absolute",
                                    "left": "0",
                                    "top": "0",
                                    "background-color": "#1d1c1f",
                                },
                                figure=figures.compute_heatmap_per_mz(
                                    slice_index, 600, 605, binary_string=False
                                ),
                            ),
                            # dmc.Group(
                            #     spacing="xs",
                            #     align="flex-end",
                            #     children=[
                            dmc.Group(
                                direction="column",
                                spacing=0,
                                style={"left": "1%", "top": "1em",},
                                class_name="position-absolute",
                                children=[
                                    html.Div(
                                        children=" Lipid selection", className="fs-5 text-light",
                                    ),
                                    dmc.Group(
                                        spacing="xs",
                                        align="flex-start",
                                        children=[
                                            dmc.MultiSelect(
                                                id="page-2-dropdown-lipids",
                                                data=return_pickled_object(
                                                    "annotations/",
                                                    "lipid_options",
                                                    force_update=False,
                                                    compute_function=return_lipid_options,
                                                ),
                                                searchable=True,
                                                nothingFound="No lipid found",
                                                radius="md",
                                                size="xs",
                                                # variant="filled",
                                                placeholder="Choose up to 3 lipids",
                                                clearable=False,
                                                maxSelectedValues=3,
                                                transitionDuration=150,
                                                transition="pop-top-left",
                                                transitionTimingFunction="ease",
                                                style={"width": "20em",},
                                            ),
                                            dmc.Button(
                                                children="Display as RGB",
                                                id="tab-2-rgb-button",
                                                variant="filled",
                                                color="gray",
                                                radius="md",
                                                size="xs",
                                                disabled=True,
                                                compact=False,
                                                loading=False,
                                            ),
                                            dmc.Button(
                                                children="Display as colormap",
                                                id="tab-2-colormap-button",
                                                variant="filled",
                                                color="gray",
                                                radius="md",
                                                size="xs",
                                                disabled=True,
                                                compact=False,
                                                loading=False,
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            #     ],
                            # ),
                            html.Div(
                                id="page-2-badge-input",
                                children=" Current input: " + "m/z boundaries",
                                className="fs-5 text-light position-absolute",
                                style={"right": "1%", "top": "1em"},
                            ),
                            dmc.Badge(
                                id="page-2-badge-lipid-1",
                                children="name-lipid-1",
                                color="red",
                                variant="filled",
                                class_name="d-none",
                                style={"right": "1%", "top": "4em"},
                            ),
                            dmc.Badge(
                                id="page-2-badge-lipid-2",
                                children="name-lipid-2",
                                color="teal",
                                variant="filled",
                                class_name="d-none",
                                style={"right": "1%", "top": "6em"},
                            ),
                            dmc.Badge(
                                id="page-2-badge-lipid-3",
                                children="name-lipid-3",
                                color="blue",
                                variant="filled",
                                class_name="d-none",
                                style={"right": "1%", "top": "8em"},
                            ),
                            dmc.Group(
                                spacing="xs",
                                align="flex-end",
                                children=[
                                    dmc.Group(
                                        # position="center",
                                        direction="column",
                                        spacing=0,
                                        children=[
                                            html.Div(
                                                children=" Lower bound (m/z)",
                                                className="fs-5 text-light",
                                            ),
                                            dmc.Tooltip(
                                                wrapLines=True,
                                                width=220,
                                                withArrow=True,
                                                transition="fade",
                                                transitionDuration=200,
                                                label="Your selection can't exceed a range of 10m/z, and must be comprised in-between 400 and 1200.",
                                                children=[
                                                    dmc.NumberInput(
                                                        id="page-2-lower-bound",
                                                        min=380,
                                                        max=1220,
                                                        precision=3,
                                                        radius="md",
                                                        size="xs",
                                                        value=600,
                                                        # variant="filled",
                                                        hideControls=True,
                                                        # label="Lower bound (m/z)",
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                    dmc.Group(
                                        # position="center",
                                        direction="column",
                                        spacing=0,
                                        children=[
                                            html.Div(
                                                children=" Upper bound (m/z)",
                                                className="fs-5 text-light",
                                            ),
                                            dmc.Tooltip(
                                                wrapLines=True,
                                                width=220,
                                                withArrow=True,
                                                transition="fade",
                                                transitionDuration=200,
                                                label="Your selection can't exceed a range of 10m/z, and must be comprised in-between 400 and 1200.",
                                                children=[
                                                    dmc.NumberInput(
                                                        id="page-2-upper-bound",
                                                        min=380,
                                                        max=1220,
                                                        precision=3,
                                                        radius="md",
                                                        size="xs",
                                                        value=602,
                                                        # variant="filled",
                                                        hideControls=True,
                                                        # label="Upper bound (m/z)",
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                    dmc.Button(
                                        children="Display as colormap",
                                        id="page-2-button-bounds",
                                        variant="filled",
                                        color="gray",
                                        radius="md",
                                        size="xs",
                                        compact=False,
                                        loading=False,
                                    ),
                                ],
                                style={"width": "35em", "left": "1%", "bottom": "1em",},
                                class_name="position-absolute",
                            ),
                            dmc.Group(
                                position="right",
                                direction="column",
                                style={"right": "1%", "bottom": "1em",},
                                class_name="position-absolute",
                                spacing=0,
                                children=[
                                    dmc.Button(
                                        children="Download data",
                                        id="tab-2-download-data-button",
                                        variant="filled",
                                        disabled=True,
                                        color="gray",
                                        radius="md",
                                        size="xs",
                                        compact=False,
                                        loading=False,
                                    ),
                                    dmc.Button(
                                        children="Download image",
                                        id="tab-2-download-image-button",
                                        variant="filled",
                                        disabled=True,
                                        color="gray",
                                        radius="md",
                                        size="xs",
                                        compact=False,
                                        loading=False,
                                        class_name="mt-1",
                                    ),
                                ],
                            ),
                            dcc.Download(id="tab-2-download-data"),
                        ],
                    ),
                ),
                #     ],
                # ),
                #             ],
                #         ),
                #     ],
                # ),
                dbc.Card(
                    style={
                        "maxWidth": "100%",
                        "margin": "0 auto",
                        "width": "100%",
                        "height": "100%",
                    },
                    className="d-none",
                    id="page-2-card-low-res",
                    children=[
                        dbc.CardHeader("Low-resolution mass-spectrometry spectrum"),
                        dbc.CardBody(
                            children=[
                                html.Div(
                                    className="loading-wrapper",
                                    children=[
                                        dbc.Spinner(
                                            color="dark",
                                            children=[
                                                html.Div(
                                                    # className="px-3 mt-2",
                                                    children=[
                                                        dcc.Graph(
                                                            id="page-2-graph-low-resolution-spectrum",
                                                            figure=figures.compute_spectrum_low_res(
                                                                slice_index
                                                            ),
                                                            style={
                                                                "height": HEIGHT_PLOTS,
                                                                "width": "100%",
                                                            },
                                                            responsive=True,
                                                            config=basic_config
                                                            | {
                                                                "toImageButtonOptions": {
                                                                    "format": "png",
                                                                    "filename": "full_spectrum_low_res",
                                                                    "scale": 2,
                                                                }
                                                            },
                                                        ),
                                                    ],
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
                dbc.Card(
                    style={
                        "maxWidth": "100%",
                        "margin": "0 auto",
                        "width": "100%",
                        "height": "100%",
                    },
                    className="d-none",
                    id="page-2-card-high-res",
                    children=[
                        dbc.CardHeader("High-resolution mass-spectrometry spectrum"),
                        dbc.CardBody(
                            children=[
                                html.Div(
                                    className="loading-wrapper",
                                    children=[
                                        dbc.Spinner(
                                            color="dark",
                                            children=[
                                                html.Div(
                                                    className="",
                                                    children=[
                                                        html.Div(
                                                            id="page-2-alert",
                                                            className="text-center mt-2",
                                                            children=html.Strong(
                                                                children="Please select a lipid or zoom more on the left graph to display the high-resolution spectrum",
                                                                style={"color": "#df5034"},
                                                            ),
                                                        ),
                                                    ],
                                                ),
                                                dcc.Graph(
                                                    id="page-2-graph-high-resolution-spectrum",
                                                    style={"display": "none"},
                                                    config=basic_config
                                                    | {
                                                        "toImageButtonOptions": {
                                                            "format": "png",
                                                            "filename": "spectrum_selection_high_res",
                                                            "scale": 2,
                                                        }
                                                    },
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    )

    return page


###### APP CALLBACKS ######

# # Function to update the heatmap toast name
# @app.app.callback(
#     Output("page-2-toast-graph-heatmap-mz-selection", "children"), Input("main-slider", "value"),
# )
# def page_2_update_graph_heatmap_mz_selection(slice_index):
#     if slice_index is not None:
#         return [
#             html.Div("Brain slice n°" + str(slice_index)),
#         ]

#     else:
#         return dash.no_update


# Function to plot page-2-graph-heatmap-mz-selection when its state get updated
@app.app.callback(
    Output("page-2-graph-heatmap-mz-selection", "figure"),
    Output("page-2-badge-input", "children"),
    Input("main-slider", "value"),
    Input("boundaries-high-resolution-mz-plot", "data"),
    Input("boundaries-low-resolution-mz-plot", "data"),
    State("page-2-selected-lipid-1", "data"),
    State("page-2-selected-lipid-2", "data"),
    State("page-2-selected-lipid-3", "data"),
    Input("tab-2-rgb-button", "n_clicks"),
    Input("tab-2-colormap-button", "n_clicks"),
    # Input("page-2-button-range", "n_clicks"),
    Input("page-2-button-bounds", "n_clicks"),
    State("page-2-lower-bound", "value"),
    State("page-2-upper-bound", "value"),
    # State("page-2-mz-value", "value"),
    # State("page-2-mz-range", "value"),
    State("page-2-badge-input", "children"),
)
def page_2_plot_graph_heatmap_mz_selection(
    slice_index,
    bound_high_res,
    bound_low_res,
    lipid_1_index,
    lipid_2_index,
    lipid_3_index,
    # colorbool,
    n_clicks_button_rgb,
    n_clicks_button_colormap,
    # n_clicks_button_range,
    n_clicks_button_bounds,
    lb,
    hb,
    # mz,
    # mz_range,
    graph_input,
):
    logging.info("Entering function to plot heatmap or RGB depending on lipid selection")
    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    # # case a mz value and a manual range have been inputed
    # if id_input == "page-2-button-range" or (
    #     id_input == "main-slider" and graph_input == "Current input: " + "m/z range"
    # ):
    #     if mz is not None and mz_range is not None:
    #         mz = float(mz)
    #         mz_range = float(mz_range)
    #         if mz > 400 and mz < 1200 and mz_range < 10:
    #             # ? Could I not use return_heatmap_per_lipid_selection instead ?
    #             return (
    #                 figures.compute_heatmap_per_mz(
    #                     slice_index, mz - mz_range / 2, mz + mz_range / 2, binary_string=False
    #                 ),
    #                 "Current input: " + "m/z range",
    #             )
    #
    #    return dash.no_update

    # case a two mz bounds values have been inputed
    if id_input == "page-2-button-bounds" or (
        id_input == "main-slider" and graph_input == "Current input: " + "m/z boundaries"
    ):
        if lb is not None and hb is not None:
            lb, hb = float(lb), float(hb)
            if lb > 400 and hb < 1200 and hb - lb > 0 and hb - lb < 10:
                return (
                    figures.compute_heatmap_per_mz(slice_index, lb, hb, binary_string=False),
                    "Current input: " + "m/z boundaries",
                )

        return dash.no_update

    # If a lipid selection has been done
    if (
        id_input == "page-2-selected-lipid-1"
        or id_input == "page-2-selected-lipid-2"
        or id_input == "page-2-selected-lipid-3"
        or id_input == "tab-2-rgb-button"
        or id_input == "tab-2-colormap-button"
        or (
            id_input == "main-slider"
            and (
                graph_input == "Current input: " + "Lipid selection colormap"
                or graph_input == "Current input: " + "Lipid selection RGB"
            )
        )
    ):
        if lipid_1_index >= 0 or lipid_2_index >= 0 or lipid_3_index >= 0:

            # Build the list of mz boundaries for each peak
            ll_lipid_bounds = [
                [
                    (
                        float(data.get_annotations().iloc[index]["min"]),
                        float(data.get_annotations().iloc[index]["max"]),
                    )
                ]
                if index != -1
                else None
                for index in [lipid_1_index, lipid_2_index, lipid_3_index]
            ]

            # Check that annotations do not intercept with each other
            l_lipid_bounds_clean = [
                x
                for l_lipid_bounds in ll_lipid_bounds
                if l_lipid_bounds is not None
                for x in l_lipid_bounds
            ]

            if len(l_lipid_bounds_clean) >= 2:
                l_t_bounds_sorted = sorted(l_lipid_bounds_clean)
                for t_bounds_1, t_bounds_2 in zip(l_t_bounds_sorted[:-1], l_t_bounds_sorted[1:]):
                    if t_bounds_1[1] > t_bounds_2[0]:
                        logging.warning("Some pixel annotations intercept each other")

            if id_input == "tab-2-colormap-button" or (
                id_input == "main-slider"
                and graph_input == "Current input: " + "Lipid selection colormap"
            ):
                return (
                    figures.compute_heatmap_per_lipid_selection(slice_index, ll_lipid_bounds),
                    "Current input: " + "Lipid selection colormap",
                )
            elif id_input == "tab-2-rgb-button" or (
                id_input == "main-slider"
                and graph_input == "Current input: " + "Lipid selection RGB"
            ):
                return (
                    figures.compute_rgb_image_per_lipid_selection(slice_index, ll_lipid_bounds),
                    "Current input: " + "Lipid selection RGB",
                )
            else:
                logging.info("Right before calling the graphing function")
                return (
                    figures.compute_rgb_image_per_lipid_selection(slice_index, ll_lipid_bounds),
                    "Current input: " + "Lipid selection RGB",
                )

        else:
            # probably the page has just been loaded, so do nothing
            # return app.slice_store.getSlice(slice_index).return_heatmap(binary_string=False)
            return dash.no_update

    # Case trigger is range slider from high resolution spectrum
    if id_input == "boundaries-high-resolution-mz-plot" or (
        id_input == "main-slider"
        and graph_input == "Current input: " + "Selection from high-res m/z graph"
    ):
        if bound_high_res is not None:
            bound_high_res = json.loads(bound_high_res)
            return (
                figures.compute_heatmap_per_mz(
                    slice_index, bound_high_res[0], bound_high_res[1], binary_string=False
                ),
                "Current input: " + "Selection from high-res m/z graph",
            )

    # Case trigger is range slider from low resolution spectrum
    if id_input == "boundaries-low-resolution-mz-plot" or (
        id_input == "main-slider"
        and graph_input == "Current input: " + "Selection from low-res m/z graph"
    ):
        if bound_low_res is not None:
            bound_low_res = json.loads(bound_low_res)
            return (
                figures.compute_heatmap_per_mz(
                    slice_index,
                    bound_low_res[0],
                    bound_low_res[1],
                    binary_string=False,
                    heatmap=False,
                    plot_contours=False,
                ),
                "Current input: " + "Selection from low-res m/z graph",
            )

    # If no trigger, it means the page has just been loaded, so load new figure with default parameters
    else:
        # return app.slice_store.getSlice(slice_index).return_heatmap(binary_string=False)
        return dash.no_update


# Function to plot page-2-graph-low-resolution-spectrum when its state get updated, i.e. when load button get clicked
@app.app.callback(
    Output("page-2-graph-low-resolution-spectrum", "figure"),
    Input("main-slider", "value"),
    State("page-2-selected-lipid-1", "data"),
    State("page-2-selected-lipid-2", "data"),
    State("page-2-selected-lipid-3", "data"),
    Input("tab-2-rgb-button", "n_clicks"),
    Input("tab-2-colormap-button", "n_clicks"),
    # Input("page-2-button-range", "n_clicks"),
    Input("page-2-button-bounds", "n_clicks"),
    State("page-2-lower-bound", "value"),
    State("page-2-upper-bound", "value"),
    # State("page-2-mz-value", "value"),
    # State("page-2-mz-range", "value"),
    State("page-2-badge-input", "children"),
    State("page-2-graph-low-resolution-spectrum", "relayoutData"),
)
def tab_2_plot_graph_low_res_spectrum(
    slice_index,
    lipid_1_index,
    lipid_2_index,
    lipid_3_index,
    n_clicks_rgb,
    n_clicks_colormap,
    # n_clicks_button_range,
    n_clicks_button_bounds,
    lb,
    hb,
    # mz,
    # mz_range,
    graph_input,
    relayoutData,
):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    # If a lipid selection has been done
    if (
        id_input == "page-2-selected-lipid-1"
        or id_input == "page-2-selected-lipid-2"
        or id_input == "page-2-selected-lipid-3"
        or id_input == "tab-2-rgb-button"
        or id_input == "tab-2-colormap-button"
        or (
            id_input == "main-slider"
            and (
                graph_input == "Current input: " + "Lipid selection colormap"
                or graph_input == "Current input: " + "Lipid selection RGB"
            )
        )
    ):

        if lipid_1_index >= 0 or lipid_2_index >= 0 or lipid_3_index >= 0:

            # build the list of mz boundaries for each peak
            l_lipid_bounds = [
                (
                    float(data.get_annotations().iloc[index]["min"]),
                    float(data.get_annotations().iloc[index]["max"]),
                )
                if index != -1
                else None
                for index in [lipid_1_index, lipid_2_index, lipid_3_index]
            ]
            return figures.compute_spectrum_low_res(slice_index, l_lipid_bounds)

        else:
            # probably the page has just been loaded, so load new figure with default parameters
            return dash.no_update
            # return figures.compute_spectrum_low_res(slice_index,)

    # elif id_input == "page-2-button-range" or (
    #     id_input == "main-slider" and graph_input == "Current input: " + "m/z range"
    # ):
    #     mz = float(mz)
    #     mz_range = float(mz_range)
    #     if mz > 400 and mz < 1200 and mz_range < 10:
    #         l_lipid_bounds = [(mz - mz_range / 2, mz + mz_range / 2), None, None]
    #         return figures.compute_spectrum_low_res(slice_index, l_lipid_bounds)

    elif id_input == "page-2-button-bounds" or (
        id_input == "main-slider" and graph_input == "Current input: " + "m/z boundaries"
    ):
        lb, hb = float(lb), float(hb)
        if lb > 400 and hb < 1200 and hb - lb > 0 and hb - lb < 10:
            l_lipid_bounds = [(lb, hb), None, None]
            return figures.compute_spectrum_low_res(slice_index, l_lipid_bounds)

    elif (
        id_input == "main-slider"
        and graph_input == "Current input: " + "Selection from low-res m/z graph"
    ):
        # TODO : find a way to set relayoutdata properly
        pass

    return dash.no_update


# Function to update the dcc store boundaries-low-resolution-mz-plot from
# value of page-2-graph-low-resolution-spectrum plot
@app.app.callback(
    Output("boundaries-low-resolution-mz-plot", "data"),
    Input("page-2-graph-low-resolution-spectrum", "relayoutData"),
    State("main-slider", "value"),
)
def page_2_store_boundaries_mz_from_graph_low_res_spectrum(relayoutData, slice_index):
    if relayoutData is not None:
        if "xaxis.range[0]" in relayoutData:
            return json.dumps([relayoutData["xaxis.range[0]"], relayoutData["xaxis.range[1]"]])
        elif "xaxis.range" in relayoutData:
            return json.dumps(relayoutData["xaxis.range"])

        # If the range is re-initialized, need to explicitely pass the first
        # and last values of the spectrum to the figure
        elif "xaxis.autorange" in relayoutData:
            return json.dumps(
                [
                    data.get_array_avg_spectrum_downsampled(slice_index)[0, 0].astype("float"),
                    data.get_array_avg_spectrum_downsampled(slice_index)[0, -1].astype("float"),
                ]
            )

    # When the app is launched, or when the plot is displayed and autoresized,
    # no boundaries are passed not to update the heatmap for nothing
    return dash.no_update


# Function to update page-2-graph-high-resolution-spectrum when the zoom is
# high-enough on page-2-graph-low-resolution-spectrum
@app.app.callback(
    Output("page-2-graph-high-resolution-spectrum", "figure"),
    Input("main-slider", "value"),
    Input("boundaries-low-resolution-mz-plot", "data"),
    State("page-2-selected-lipid-1", "data"),
    State("page-2-selected-lipid-2", "data"),
    State("page-2-selected-lipid-3", "data"),
    Input("tab-2-rgb-button", "n_clicks"),
    Input("tab-2-colormap-button", "n_clicks"),
    # Input("page-2-button-range", "n_clicks"),
    Input("page-2-button-bounds", "n_clicks"),
    State("page-2-lower-bound", "value"),
    State("page-2-upper-bound", "value"),
    # State("page-2-mz-value", "value"),
    # State("page-2-mz-range", "value"),
    State("page-2-badge-input", "children"),
)
def page_2_plot_graph_high_res_spectrum(
    slice_index,
    bound_high_res,
    lipid_1_index,
    lipid_2_index,
    lipid_3_index,
    n_clicks_rgb,
    n_clicks_colormap,
    # n_clicks_button_range,
    n_clicks_button_bounds,
    lb,
    hb,
    # mz,
    # mz_range,
    graph_input,
):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    # If a lipid selection has been done
    if (
        id_input == "page-2-selected-lipid-1"
        or id_input == "page-2-selected-lipid-2"
        or id_input == "page-2-selected-lipid-3"
        or id_input == "tab-2-rgb-button"
        or id_input == "tab-2-colormap-button"
        or id_input == "page-2-last-selected-lipids"
        or (
            id_input == "main-slider"
            and (
                graph_input == "Current input: " + "Lipid selection colormap"
                or graph_input == "Current input: " + "Lipid selection RGB"
            )
        )
    ):
        if lipid_1_index >= 0 or lipid_2_index >= 0 or lipid_3_index >= 0:

            # Build the list of mz boundaries for each peak
            l_indexes = [lipid_1_index, lipid_2_index, lipid_3_index]
            l_lipid_bounds = [
                (
                    float(data.get_annotations().iloc[index]["min"]),
                    float(data.get_annotations().iloc[index]["max"]),
                )
                if index != -1
                else None
                for index in l_indexes
            ]
            if lipid_3_index >= 0:
                current_lipid_index = 2
            elif lipid_2_index >= 0:
                current_lipid_index = 1
            else:
                current_lipid_index = 0
            return figures.compute_spectrum_high_res(
                slice_index,
                l_lipid_bounds[current_lipid_index][0] - 10 ** -2,
                l_lipid_bounds[current_lipid_index][1] + 10 ** -2,
                annotations=l_lipid_bounds,
                force_xlim=True,
            )

    # elif id_input == "page-2-button-range" or (
    #     id_input == "main-slider" and graph_input == "Current input: " + "m/z range"
    # ):
    #     mz = float(mz)
    #     mz_range = float(mz_range)
    #     if mz > 400 and mz < 1200 and mz_range < 10:
    #         # l_lipid_bounds = [(mz - mz_range / 2, mz + mz_range / 2), None, None]
    #         return figures.compute_spectrum_high_res(
    #             slice_index,
    #             mz - mz_range / 2 - 10 ** -2,
    #             mz + mz_range / 2 + 10 ** -2,
    #             # annotations=l_lipid_bounds,
    #             force_xlim=True,
    #         )

    elif id_input == "page-2-button-bounds" or (
        id_input == "main-slider" and graph_input == "Current input: " + "m/z boundaries"
    ):
        lb, hb = float(lb), float(hb)
        if lb > 400 and hb < 1200 and hb - lb > 0 and hb - lb < 10:
            # l_lipid_bounds = [(lb, hb), None, None]
            return figures.compute_spectrum_high_res(
                slice_index,
                lb - 10 ** -2,
                hb + 10 ** -2,
                force_xlim=True,  # annotations=l_lipid_bounds,
            )

    # If the figure is created at app launch or after load button is cliked, or with an empty lipid selection,
    # don't plot anything
    elif "page-2-selected-lipid" in id_input:
        return dash.no_update

    # Otherwise, if new boundaries have been selected on the low-resolution spectrum
    elif id_input == "boundaries-low-resolution-mz-plot" and bound_high_res is not None:
        bound_high_res = json.loads(bound_high_res)

        # Case the zoom is high enough
        if bound_high_res[1] - bound_high_res[0] <= 3:
            return figures.compute_spectrum_high_res(
                slice_index, bound_high_res[0], bound_high_res[1]
            )
        # Otherwise just return default (empty) graph
        else:
            return dash.no_update

    # The page has just been loaded, no spectrum is displayed
    return dash.no_update


# Function to update the dcc store boundaries-high-resolution-mz-plot
# from value of page-2-graph-high-resolution-spectrum plot
@app.app.callback(
    Output("boundaries-high-resolution-mz-plot", "data"),
    Input("page-2-graph-high-resolution-spectrum", "relayoutData"),
    Input("boundaries-low-resolution-mz-plot", "data"),
)
def page_2_store_boundaries_mz_from_graph_high_res_spectrum(relayoutData, bound_low_res):

    # Primarily update high-res boundaries with high-res range slider
    if relayoutData is not None:
        if "xaxis.range[0]" in relayoutData:
            return json.dumps([relayoutData["xaxis.range[0]"], relayoutData["xaxis.range[1]"]])
        elif "xaxis.range" in relayoutData:
            return json.dumps(relayoutData["xaxis.range"])

        # If the range is re-initialized, need to explicitely pass the low-res value of the slider to the figure
        elif "xaxis.autorange" in relayoutData:
            if bound_low_res is not None:
                bound_low_res = json.loads(bound_low_res)
                if bound_low_res[1] - bound_low_res[0] <= 3:
                    return json.dumps(bound_low_res)

    # But also needs to be updated when low-res slider is changed and is zoomed enough
    elif bound_low_res is not None:
        bound_low_res = json.loads(bound_low_res)
        if bound_low_res[1] - bound_low_res[0] <= 3:
            return json.dumps(bound_low_res)

    # Page has just been loaded, do nothing
    else:
        return dash.no_update


"""
# Function to refine dropdown names choices
@app.app.callback(
    Output("page-2-dropdown-lipid-names", "options"),
    Output("page-2-dropdown-lipid-structures", "options"),
    Output("page-2-dropdown-lipid-cations", "options"),
    # Output("page-2-dropdown-lipid-names", "value"),
    # Output("page-2-dropdown-lipid-structures", "value"),
    # Output("page-2-dropdown-lipid-cations", "value"),
    Input("main-slider", "value"),
    Input("page-2-dropdown-lipid-names", "value"),
    Input("page-2-dropdown-lipid-structures", "value"),
    State("page-2-dropdown-lipid-names", "options"),
    State("page-2-dropdown-lipid-structures", "options"),
    State("page-2-dropdown-lipid-cations", "options"),
)
def tab_2_handle_dropdowns(
    slice_index, name, structure, options_names, options_structures, options_cations
):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    # Refine dropdown hierarchically: when first one is set, the 2 other options are computed accordingly,
    # when second one is set, the last one option is computed
    if slice_index is not None:
        # if len(id_input) == 0:
        if name is None and structure is None:
            # options_names = [
            #     {"label": name, "value": name}
            #     for name in sorted(
            #         data.get_annotations()[data.get_annotations()["slice"] == slice_index].name.unique()
            #     )
            # ]
            options_names = [
                {"label": name, "value": name}
                for name in sorted(data.get_annotations().name.unique())
            ]
            return options_names, [], []  # , None, None, None

        elif name is not None:
            if id_input == "page-2-dropdown-lipid-names":
                structures = data.get_annotations()[
                    (
                        data.get_annotations()["name"] == name
                    )  # & (data.get_annotations()["slice"] == slice_index)
                ].structure.unique()
                options_structures = [
                    {"label": structure, "value": structure} for structure in sorted(structures)
                ]
                return options_names, options_structures, []  # , name, None, None

            elif structure is not None:
                if id_input == "page-2-dropdown-lipid-structures":
                    cations = data.get_annotations()[
                        (data.get_annotations()["name"] == name)
                        & (data.get_annotations()["structure"] == structure)
                        # & (data.get_annotations()["slice"] == slice_index)
                    ].cation.unique()
                    options_cations = [
                        {"label": cation, "value": cation} for cation in sorted(cations)
                    ]
                    return (
                        options_names,
                        options_structures,
                        options_cations,
                    )  # , name, structure, None

    return dash.no_update
"""

# Function to add dropdown choice to selection
@app.app.callback(
    Output("page-2-badge-lipid-1", "children"),
    Output("page-2-badge-lipid-2", "children"),
    Output("page-2-badge-lipid-3", "children"),
    Output("page-2-selected-lipid-1", "data"),
    Output("page-2-selected-lipid-2", "data"),
    Output("page-2-selected-lipid-3", "data"),
    Output("page-2-badge-lipid-1", "class_name"),
    Output("page-2-badge-lipid-2", "class_name"),
    Output("page-2-badge-lipid-3", "class_name"),
    # Output("page-2-dropdown-lipids", "value"),
    Input("page-2-dropdown-lipids", "value"),
    Input("page-2-badge-lipid-1", "class_name"),
    Input("page-2-badge-lipid-2", "class_name"),
    Input("page-2-badge-lipid-3", "class_name"),
    Input("main-slider", "value"),
    State("page-2-selected-lipid-1", "data"),
    State("page-2-selected-lipid-2", "data"),
    State("page-2-selected-lipid-3", "data"),
    State("page-2-badge-lipid-1", "children"),
    State("page-2-badge-lipid-2", "children"),
    State("page-2-badge-lipid-3", "children"),
)
def page_2_add_toast_selection(
    l_lipid_names,
    class_name_badge_1,
    class_name_badge_2,
    class_name_badge_3,
    slice_index,
    lipid_1_index,
    lipid_2_index,
    lipid_3_index,
    header_1,
    header_2,
    header_3,
):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]

    # print(id_input, value_input, l_lipid_names)

    # if page-2-dropdown-lipids is called while there's no lipid name defined, it means the page just got loaded
    if len(id_input) == 0 or (id_input == "page-2-dropdown-lipids" and l_lipid_names is None):
        return "", "", "", -1, -1, -1, "d-none", "d-none", "d-none"  # , None

    # If one or several lipids have been deleted
    if l_lipid_names is not None:
        if len(l_lipid_names) < len(
            [x for x in [lipid_1_index, lipid_2_index, lipid_3_index] if x != -1]
        ):
            logging.info("One or several lipids have been deleter. Cleaning lipid badges now.")
            for idx_header, header in enumerate([header_1, header_2, header_3]):
                found = False
                for lipid_name in l_lipid_names:
                    if lipid_name == header:
                        found = True
                if not found:
                    if idx_header == 0:
                        header_1 = ""
                        lipid_1_index = -1
                        class_name_badge_1 = "d-none"
                    if idx_header == 1:
                        header_2 = ""
                        lipid_2_index = -1
                        class_name_badge_2 = "d-none"
                    if idx_header == 2:
                        header_3 = ""
                        lipid_3_index = -1
                        class_name_badge_3 = "d-none"

            return (
                header_1,
                header_2,
                header_3,
                lipid_1_index,
                lipid_2_index,
                lipid_3_index,
                class_name_badge_1,
                class_name_badge_2,
                class_name_badge_3,
            )

    # Otherwise, update selection or add lipid
    if (
        id_input == "page-2-dropdown-lipids" and l_lipid_names is not None
    ) or id_input == "main-slider":

        if id_input == "main-slider":

            # for each lipid, get lipid name, structure and cation
            for header in [header_1, header_2, header_3]:

                if len(header) > 2:
                    name, structure, cation = header.split(" ")

                    # Find lipid location
                    l_lipid_loc_temp = (
                        data.get_annotations()
                        .index[
                            (data.get_annotations()["name"] == name)
                            & (data.get_annotations()["structure"] == structure)
                            & (data.get_annotations()["cation"] == cation)
                        ]
                        .tolist()
                    )
                    l_lipid_loc = [
                        l_lipid_loc_temp[i]
                        for i, x in enumerate(
                            data.get_annotations().iloc[l_lipid_loc_temp]["slice"] == slice_index
                        )
                        if x
                    ]

                    # Fill list with first annotation that exists if it can't find one for the current slice
                    if len(l_lipid_loc) == 0:
                        l_lipid_loc = l_lipid_loc_temp[:1]

                    # Record location and lipid name
                    lipid_index = l_lipid_loc[0]

                    # If lipid has already been selected before, replace the index
                    if header_1 == header:
                        lipid_1_index = lipid_index
                    elif header_2 == header:
                        lipid_2_index = lipid_index
                    elif header_3 == header:
                        lipid_3_index = lipid_index

            return (
                header_1,
                header_2,
                header_3,
                lipid_1_index,
                lipid_2_index,
                lipid_3_index,
                class_name_badge_1,
                class_name_badge_2,
                class_name_badge_3,
                # None,
            )

        elif id_input == "page-2-dropdown-lipids":
            # Get the lipid name and structure
            name, structure, cation = l_lipid_names[-1].split(" ")

            # Find lipid location
            l_lipid_loc = (
                data.get_annotations()
                .index[
                    (data.get_annotations()["name"] == name)
                    & (data.get_annotations()["structure"] == structure)
                    & (data.get_annotations()["slice"] == slice_index)
                    & (data.get_annotations()["cation"] == cation)
                ]
                .tolist()
            )

            # If several lipids correspond to the selection, we have a problem...
            if len(l_lipid_loc) > 1:
                logging.warning("More than one lipid corresponds to the selection")
                l_lipid_loc = [l_lipid_loc[-1]]

            if len(l_lipid_loc) < 1:
                logging.warning("No lipid annotation exist. Taking another slice annotation")
                l_lipid_loc = (
                    data.get_annotations()
                    .index[
                        (data.get_annotations()["name"] == name)
                        & (data.get_annotations()["structure"] == structure)
                        & (data.get_annotations()["cation"] == cation)
                    ]
                    .tolist()
                )[:1]
                # return dash.no_update

            # Record location and lipid name
            lipid_index = l_lipid_loc[0]
            lipid_string = name + " " + structure + " " + cation

            change_made = False

            # If lipid has already been selected before, replace the index
            if header_1 == lipid_string:
                lipid_1_index = lipid_index
                change_made = True
            elif header_2 == lipid_string:
                lipid_2_index = lipid_index
                change_made = True
            elif header_3 == lipid_string:
                lipid_3_index = lipid_index
                change_made = True

            # If it's a new lipid selection, fill the first available header
            if lipid_string not in [header_1, header_2, header_2]:

                # Check first slot available
                if class_name_badge_1 == "d-none":
                    header_1 = lipid_string
                    lipid_1_index = lipid_index
                    class_name_badge_1 = "position-absolute"
                elif class_name_badge_2 == "d-none":
                    header_2 = lipid_string
                    lipid_2_index = lipid_index
                    class_name_badge_2 = "position-absolute"
                elif class_name_badge_3 == "d-none":
                    header_3 = lipid_string
                    lipid_3_index = lipid_index
                    class_name_badge_3 = "position-absolute"
                else:
                    logging.warning("More than 3 lipids have been selected")
                    return dash.no_update
                change_made = True

            if change_made:
                logging.info(
                    "Changes have been made to the lipid selection or indexation, propagating callback."
                )
                return (
                    header_1,
                    header_2,
                    header_3,
                    lipid_1_index,
                    lipid_2_index,
                    lipid_3_index,
                    class_name_badge_1,
                    class_name_badge_2,
                    class_name_badge_3,
                    # None,
                )
            else:
                return dash.no_update

    return dash.no_update


# Function to make visible the high-res m/z plot in tab 2
@app.app.callback(
    Output("page-2-graph-high-resolution-spectrum", "style"),
    Input("page-2-graph-high-resolution-spectrum", "figure"),
)
def tab_2_display_high_res_mz_plot(figure):
    if figure is not None:
        if figure["data"][0]["x"] != [[]]:
            return {"height": HEIGHT_PLOTS}
            # return {"height": "100%"}

    return {"display": "none"}


# Function to make visible the alert regarding the high-res m/z plot in tab 2
@app.app.callback(
    Output("page-2-alert", "style"), Input("page-2-graph-high-resolution-spectrum", "figure"),
)
def tab_2_display_alert(figure):
    if figure is not None:
        if figure["data"][0]["x"] != [[]]:
            return {"display": "none"}
    return {}


@app.app.callback(
    Output("tab-2-download-data", "data"),
    Input("tab-2-download-data-button", "n_clicks"),
    State("page-2-selected-lipid-1", "data"),
    State("page-2-selected-lipid-2", "data"),
    State("page-2-selected-lipid-3", "data"),
    State("main-slider", "value"),
    prevent_initial_call=True,
)
def tab_2_download(n_clicks, lipid_1_index, lipid_2_index, lipid_3_index, slice_index):

    l_lipids_indexes = [
        x for x in [lipid_1_index, lipid_2_index, lipid_3_index] if x is not None and x != -1
    ]
    # If lipids has been selected from the dropdown, filter them in the df and download them
    if len(l_lipids_indexes) > 0:

        def to_excel(bytes_io):
            xlsx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
            data.get_annotations().iloc[l_lipids_indexes].to_excel(
                xlsx_writer, index=False, sheet_name="Selected lipids"
            )
            for i, index in enumerate(l_lipids_indexes):
                name = (
                    data.get_annotations().iloc[index]["name"]
                    + "_"
                    + data.get_annotations().iloc[index]["structure"]
                    + "_"
                    + data.get_annotations().iloc[index]["cation"]
                )

                # Need to clean name to use it as a sheet name
                name = name.replace(":", "").replace("/", "")
                lb = float(data.get_annotations().iloc[index]["min"]) - 10 ** -2
                hb = float(data.get_annotations().iloc[index]["max"]) + 10 ** -2
                x, y = figures.compute_spectrum_high_res(slice_index, lb, hb, plot=False)
                df = pd.DataFrame.from_dict({"m/z": x, "Intensity": y})
                df.to_excel(xlsx_writer, index=False, sheet_name=name[:31])
            xlsx_writer.save()

        return dcc.send_data_frame(to_excel, "my_lipid_selection.xlsx")
    else:
        return dash.no_update


@app.app.callback(
    Output("tab-2-download-data-button", "disabled"),
    Output("tab-2-rgb-button", "disabled"),
    Output("tab-2-colormap-button", "disabled"),
    Input("page-2-selected-lipid-1", "data"),
    Input("page-2-selected-lipid-2", "data"),
    Input("page-2-selected-lipid-3", "data"),
)
def tab_2_active_download(lipid_1_index, lipid_2_index, lipid_3_index):
    l_lipids_indexes = [
        x for x in [lipid_1_index, lipid_2_index, lipid_3_index] if x is not None and x != -1
    ]
    # If lipids has been selected from the dropdown, activate button
    if len(l_lipids_indexes) > 0:
        return False, False, False
    else:
        return True, True, True


"""
# Function to disable/enable dropdowns depending on the number of lipids selected
@app.app.callback(
    Output("page-2-dropdown-lipid-names", "disabled"),
    Output("page-2-dropdown-lipid-structures", "disabled"),
    Output("page-2-dropdown-lipid-cations", "disabled"),
    Output("page-2-warning-lipids-number", "className"),
    Input("page-2-selected-lipid-1", "data"),
    Input("page-2-selected-lipid-2", "data"),
    Input("page-2-selected-lipid-3", "data"),
)
def tab_2_disable_dropdowns(lipid_1_index, lipid_2_index, lipid_3_index):

    # If all slots are taken, disable all dropdowns
    if lipid_1_index != -1 and lipid_2_index != -1 and lipid_3_index != -1:
        return True, True, True, "mt-1 text-center"
    else:
        return False, False, False, "mt-1 text-center d-none"
"""

"""
@app.app.callback(
    Output("page-2-button-range", "disabled"),
    Input("page-2-mz-value", "value"),
    Input("page-2-mz-range", "value"),
)
def tab_2_button_range(mz, mz_range):
    if mz is not None and mz_range is not None:
        mz = float(mz)
        mz_range = float(mz_range)
        if mz > 400 and mz < 1200 and mz_range < 10:
            return False
    return True
"""


@app.app.callback(
    Output("page-2-button-bounds", "disabled"),
    Input("page-2-lower-bound", "value"),
    Input("page-2-upper-bound", "value"),
)
def tab_2_button_window(lb, hb):
    if lb is not None and hb is not None:
        lb, hb = float(lb), float(hb)
        if lb > 400 and hb < 1200 and hb - lb > 0 and hb - lb < 10:
            return False
    return True


### Not a callback but still needed
def return_lipid_options():
    return [
        {
            "label": name + " " + structure + " " + cation,
            "value": name + " " + structure + " " + cation,
            "group": name,
        }
        for name in sorted(data.get_annotations().name.unique())
        for structure in sorted(
            data.get_annotations()[(data.get_annotations()["name"] == name)].structure.unique()
        )
        for cation in sorted(
            data.get_annotations()[
                (data.get_annotations()["name"] == name)
                & (data.get_annotations()["structure"] == structure)
            ].cation.unique()
        )
    ]

