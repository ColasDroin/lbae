###### IMPORT MODULES ######

# Official modules
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import logging
import copy

# Homemade modules
from lbae import app
from lbae.app import figures, data, atlas
from lbae import config
from lbae.modules.tools.misc import return_pickled_object, convert_image_to_base64
from lbae.modules.tools.spectra import (
    sample_rows_from_path,
    compute_spectrum_per_row_selection,
    convert_array_to_fine_grained,
    strip_zeros,
    return_index_labels,
    add_zeros_to_spectrum,
    compute_avg_intensity_per_lipid,
)

HEIGHT_PLOTS = 280
N_LINES = int(np.ceil(HEIGHT_PLOTS / 30))


###### DEFFINE PAGE LAYOUT ######


def return_layout(basic_config, slice_index=1):

    page = html.Div(
        children=[
            ### First row
            dbc.Row(
                justify="center",
                children=[
                    ## First column
                    dbc.Col(
                        # xl=6,
                        xs=12,
                        md=12,
                        lg=12,
                        xl=12,
                        xxl=11,
                        children=[
                            dbc.Card(
                                style={"maxWidth": "100%", "margin": "0 auto"},
                                children=[
                                    dbc.CardHeader(
                                        className="d-flex justify-content-between",
                                        children=[
                                            html.Div(
                                                id="page-3-toast-graph-heatmap-mz-selection", children="Brain slice n°"
                                            ),
                                        ],
                                    ),
                                    dbc.CardBody(
                                        className="loading-wrapper pt-0 mt-0 pb-0 mb-1 px-0 mx-0",
                                        children=[
                                            ### First nested row
                                            dbc.Row(
                                                justify="center",
                                                children=[
                                                    ## First column of nested row
                                                    dbc.Col(
                                                        width=4,
                                                        className="mt-1 pt-0",
                                                        children=[
                                                            html.Div(
                                                                className="page-1-fixed-aspect-ratio",
                                                                children=[
                                                                    dcc.Graph(
                                                                        id="page-3-graph-atlas-per-sel",
                                                                        config=basic_config
                                                                        | {"displayModeBar": False},
                                                                        style={
                                                                            "width": "100%",
                                                                            "height": "100%",
                                                                            "position": "absolute",
                                                                            "left": "0",
                                                                        },
                                                                        figure=return_pickled_object(
                                                                            "figures/load_page",
                                                                            "figure_basic_image",
                                                                            force_update=False,
                                                                            compute_function=figures.compute_figure_basic_image,
                                                                            type_figure=None,
                                                                            index_image=slice_index - 1,
                                                                            plot_atlas_contours=True,
                                                                            only_contours=True,
                                                                        ),
                                                                    ),
                                                                    html.P(
                                                                        "Hovered region: ",
                                                                        id="page-3-graph-atlas-hover-text",
                                                                        className="text-warning font-weight-bold position-absolute",
                                                                        style={"left": "15%", "top": "1em"},
                                                                    ),
                                                                ],
                                                            ),
                                                            ### First nested row
                                                            dbc.Row(
                                                                justify="center",
                                                                className="d-flex align-items-center mt-1 pt-0",
                                                                children=[
                                                                    ## First column of nested row
                                                                    dbc.Col(
                                                                        width=12,
                                                                        className="d-flex justify-content-center",
                                                                        children=[
                                                                            html.Div(
                                                                                style={
                                                                                    "width": "80%",
                                                                                },  # "minWidth": "8em",},
                                                                                children=dcc.Dropdown(
                                                                                    id="page-3-dropdown-brain-regions",
                                                                                    options=[
                                                                                        {"label": node, "value": node}
                                                                                        for node in return_pickled_object(
                                                                                            "atlas/atlas_objects",
                                                                                            "hierarchy",
                                                                                            force_update=False,
                                                                                            compute_function=atlas.compute_hierarchy_list,
                                                                                        )[
                                                                                            0
                                                                                        ]
                                                                                    ],
                                                                                    placeholder="Click on brain regions above.",
                                                                                    multi=True,
                                                                                    clearable=False,
                                                                                    disabled=True,
                                                                                    # className="ml-5",
                                                                                ),
                                                                            ),
                                                                        ],
                                                                    ),
                                                                    ## Second column of nested row
                                                                    dbc.Col(
                                                                        width=12,
                                                                        className="d-flex justify-content-center mt-1",
                                                                        children=[
                                                                            html.Div(
                                                                                className="d-grid gap-2 col-10 mx-auto",
                                                                                children=[
                                                                                    dbc.Button(
                                                                                        children="Compute spectra",
                                                                                        id="page-3-button-compute-spectra",
                                                                                        disabled=True,
                                                                                        className="",
                                                                                        color="primary",
                                                                                    ),
                                                                                ],
                                                                            ),
                                                                        ],
                                                                    ),
                                                                    ## Third column of nested row
                                                                    dbc.Col(
                                                                        width=12,
                                                                        className="d-flex justify-content-center mt-2",
                                                                        children=[
                                                                            html.Div(
                                                                                className="d-grid gap-2 col-10 mx-auto",
                                                                                children=[
                                                                                    dbc.Button(
                                                                                        children="Download spectrum data",
                                                                                        id="tab-3-download-data-button",
                                                                                        disabled=True,
                                                                                        className="",
                                                                                        color="primary",
                                                                                    ),
                                                                                ],
                                                                            ),
                                                                        ],
                                                                    ),
                                                                    dcc.Download(id="tab-3-download-data"),
                                                                    ## Fourth column of nested row
                                                                    dbc.Col(
                                                                        width=12,
                                                                        className="d-flex justify-content-center mt-2",
                                                                        children=[
                                                                            html.Div(
                                                                                className="d-grid gap-2 col-10 mx-auto",
                                                                                children=[
                                                                                    dbc.Button(
                                                                                        children="Reset",
                                                                                        id="page-3-reset-button",
                                                                                        color="primary",
                                                                                    )
                                                                                ],
                                                                            ),
                                                                        ],
                                                                    ),
                                                                    ## Fifth column of nested row
                                                                    dbc.Col(
                                                                        width=12,
                                                                        className="d-flex flex-row justify-content-center mt-2",
                                                                        children=[
                                                                            dbc.Switch(
                                                                                id="page-3-normalize",
                                                                                label="Normalize",
                                                                                value=False,
                                                                                className="mr-1",
                                                                            ),
                                                                            dbc.Switch(
                                                                                id="page-3-log",
                                                                                label="Log-transform",
                                                                                value=False,
                                                                                className="ml-1",
                                                                            ),
                                                                        ],
                                                                    ),
                                                                    ### End of first nested row
                                                                ],
                                                            ),
                                                        ],
                                                    ),
                                                    ## Second column of nested row
                                                    dbc.Col(
                                                        width=8,
                                                        className="mx-0 px-0",
                                                        children=[
                                                            html.Div(
                                                                className="fixed-aspect-ratio",
                                                                children=[
                                                                    dcc.Graph(
                                                                        id="page-3-graph-heatmap-per-sel",
                                                                        config=basic_config
                                                                        | {
                                                                            "toImageButtonOptions": {
                                                                                "format": "png",
                                                                                "filename": "annotated_brain_slice",
                                                                                "scale": 2,
                                                                            }
                                                                        },
                                                                        style={
                                                                            "width": "100%",
                                                                            "height": "100%",
                                                                            "position": "absolute",
                                                                            "left": "0",
                                                                        },
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
                                                                    html.P(
                                                                        "Hovered region: ",
                                                                        id="page-3-graph-hover-text",
                                                                        className="text-warning font-weight-bold position-absolute",
                                                                        style={"left": "15%", "top": "1em"},
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
                            ## End of first column
                        ],
                    ),
                    ### End of first row
                ],
            ),
            ### Second row
            dbc.Row(
                justify="center",
                children=dbc.Col(
                    xs=8, children=dbc.Progress(value=0, id="page-3-progress", animated=True, striped=True)
                ),
            ),
            dbc.Row(
                id="page-3-row-main-computations",
                justify="center",
                children=[
                    ##First column
                    dbc.Col(
                        xs=12,
                        md=9,
                        xxl=8,
                        children=[
                            dbc.Card(
                                style={"maxWidth": "100%", "margin": "0 auto"},
                                className="mt-4",
                                children=[
                                    dbc.CardHeader("High-resolution spectrum for current selection"),
                                    dbc.CardBody(
                                        className="loading-wrapper py-0",
                                        children=[
                                            html.Div(
                                                children=[
                                                    dbc.Spinner(
                                                        color="dark",
                                                        children=[
                                                            html.Div(
                                                                className="px-5",
                                                                children=[
                                                                    html.Div(
                                                                        id="page-3-alert",
                                                                        className="text-center my-2",
                                                                        children=html.Strong(
                                                                            children="Please draw at least one region on the heatmap and clicked on 'compute spectra'.. and clicked on 'compute spectra'.",
                                                                            style={"color": "#df5034"},
                                                                        ),
                                                                    ),
                                                                    html.Div(
                                                                        id="page-3-alert-2",
                                                                        className="text-center my-2",
                                                                        style={"display": "none"},
                                                                        children=[
                                                                            html.Strong(
                                                                                children="Too many regions selected, please reset the annotations.",
                                                                                style={"color": "#df5034"},
                                                                            ),
                                                                        ],
                                                                    ),
                                                                ],
                                                            ),
                                                            html.Div(id="page-3-graph-spectrum-per-pixel-wait"),
                                                            dcc.Graph(
                                                                id="page-3-graph-spectrum-per-pixel",
                                                                style={"height": HEIGHT_PLOTS} | {"display": "none"},
                                                                config=basic_config
                                                                | {
                                                                    "toImageButtonOptions": {
                                                                        "format": "png",
                                                                        "filename": "spectrum_from_custom_region",
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
                    ## Second column
                    dbc.Col(
                        xs=12,
                        md=3,
                        xl=3,
                        xxl=3,
                        children=[
                            dbc.Card(
                                # style={"maxWidth": "100%", "margin": "0 auto"},
                                className="mt-4",
                                children=[
                                    dbc.CardHeader("Lipid comparison"),
                                    dbc.CardBody(
                                        # className="loading-wrapper  py-0",
                                        className="py-0",
                                        children=[
                                            dbc.Spinner(
                                                color="sucess",
                                                delay_hide=100,
                                                children=[
                                                    html.Div(
                                                        id="page-3-alert-4",
                                                        className="text-center my-2",
                                                        children=html.Strong(
                                                            children="Please draw at least one region on the heatmap and clicked on 'compute spectra'..",
                                                            style={"color": "#df5034"},
                                                        ),
                                                    ),
                                                    html.Div(id="page-3-div-dropdown-wait"),
                                                    html.Div(
                                                        id="page-3-div-dropdown",
                                                        style={"display": "none"},
                                                        # className="loading-wrapper",
                                                        children=[
                                                            dcc.Dropdown(
                                                                id="page-3-dropdown-red",
                                                                options=[],
                                                                value=[],
                                                                multi=True,
                                                            ),
                                                            # html.Hr(className="my-2"),
                                                            dcc.Dropdown(
                                                                id="page-3-dropdown-green",
                                                                options=[],
                                                                value=[],
                                                                multi=True,
                                                            ),
                                                            # html.Hr(className="my-2"),
                                                            dcc.Dropdown(
                                                                id="page-3-dropdown-blue",
                                                                options=[],
                                                                value=[],
                                                                multi=True,
                                                            ),
                                                            html.Hr(className="my-2"),
                                                            html.P(
                                                                className="lead d-flex justify-content-center",
                                                                children=[
                                                                    dbc.Button(
                                                                        id="page-3-open-modal",
                                                                        children="Visualize and compare",
                                                                        color="primary",
                                                                        disabled=True,
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
                                # style={"maxWidth": "100%", "margin": "0 auto"},
                                className="mt-1",
                                children=[
                                    dbc.CardHeader("Lipid filtering per percentile"),
                                    dbc.CardBody(
                                        # className="loading-wrapper  py-0",
                                        className="py-0",
                                        children=[
                                            dcc.Slider(
                                                id="page-4-slider",
                                                min=0,
                                                max=99,
                                                value=10,
                                                marks={
                                                    0: {"label": "No filtering"},
                                                    25: {"label": "25%"},
                                                    50: {"label": "50%"},
                                                    75: {"label": "75%"},
                                                    99: {"label": "99%", "style": {"color": "#f50"}},
                                                },
                                            )
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ### End of second row
                    ## First column
                    dbc.Col(
                        className="mt-2",
                        xl=4,
                        md=4,
                        xs=12,
                        children=[
                            dbc.Card(
                                # style={"maxWidth": "100%", "margin": "0 auto"},
                                children=[
                                    dbc.CardHeader("Average lipid expression per selection"),
                                    dbc.CardBody(
                                        className="loading-wrapper py-0",
                                        children=[
                                            html.Div(
                                                id="page-3-alert-3",
                                                className="text-center my-2",
                                                children=html.Strong(
                                                    children="Please draw at least one region on the heatmap and clicked on 'compute spectra'.",
                                                    style={"color": "#df5034"},
                                                ),
                                            ),
                                            html.Div(
                                                children=[
                                                    dbc.Spinner(
                                                        color="sucess",
                                                        children=[
                                                            html.Div(id="page-3-graph-heatmap-per-lipid-wait"),
                                                            dcc.Graph(
                                                                id="page-3-graph-heatmap-per-lipid",
                                                                className="mb-1",
                                                                style={"height": 2 * HEIGHT_PLOTS}
                                                                | {"display": "none"},
                                                                config=basic_config
                                                                | {
                                                                    "toImageButtonOptions": {
                                                                        "format": "png",
                                                                        "filename": "annotated_brain_slice",
                                                                        "scale": 2,
                                                                    }
                                                                },
                                                            ),
                                                            html.Div(
                                                                id="page-3-switches",
                                                                className="d-none",
                                                                children=[
                                                                    # dbc.Checklist(
                                                                    #    options=[
                                                                    #        {"label": "mean-rescale", "value": True,}
                                                                    #    ],
                                                                    #    id="page-3-scale-by-mean-switch",
                                                                    #    switch=True,
                                                                    #    value=[],
                                                                    #    className="mr-5",
                                                                    # ),
                                                                    dbc.Checklist(
                                                                        options=[
                                                                            {
                                                                                "label": "Sort by relative std",
                                                                                "value": True,
                                                                            }
                                                                        ],
                                                                        id="page-3-sort-by-diff-switch",
                                                                        switch=True,
                                                                        value=[True],
                                                                        className="ml-5",
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
                        ],
                    ),
                    ## Second column
                    dbc.Col(
                        xxl=7,
                        md=8,
                        xs=12,
                        className="mt-2",
                        children=[
                            dbc.Card(
                                style={"maxWidth": "100%", "margin": "0 auto"},
                                children=[
                                    dbc.CardHeader(
                                        className="d-flex justify-content-between",
                                        children=[
                                            html.Div("Lipid intensity comparison", className="mr-5"),
                                            dbc.Switch(
                                                id="page-3-toggle-mask",
                                                label="Toggle masks and shape display",
                                                value=False,
                                                className="ml-5",
                                            ),
                                        ],
                                    ),
                                    dbc.CardBody(
                                        id="page-3-graph-lipid-comparison",
                                        className="loading-wrapper pt-0 mt-0 pb-0 mb-1 px-0 mx-0",
                                        children=[
                                            html.Div(
                                                id="page-3-alert-5",
                                                className="text-center my-2",
                                                children=html.Strong(
                                                    children="Please draw at least one region on the heatmap and clicked on 'compute spectra'..",
                                                    style={"color": "#df5034"},
                                                ),
                                            ),
                                            dbc.Spinner(
                                                color="dark",
                                                children=[
                                                    html.Div(id="page-3-graph-lipid--comparison-wait"),
                                                    html.Div(
                                                        className="page-1-fixed-aspect-ratio",
                                                        id="page-3-div-graph-lipid-comparison",
                                                        style={"display": "none"},
                                                        children=[
                                                            dcc.Graph(
                                                                id="page-3-heatmap-lipid-comparison",
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
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ### End of third row
                ],
            ),
        ]
    )

    return page


###### APP CALLBACKS ######

# Function to update the heatmap toast name
@app.app.callback(
    Output("page-3-toast-graph-heatmap-mz-selection", "children"), Input("main-slider", "value"),
)
def page_3_plot_graph_heatmap_mz_selection(slice_index):
    if slice_index is not None:
        return "Brain slice n°" + str(slice_index)
    else:
        return dash.no_update


@app.app.callback(
    Output("page-3-graph-hover-text", "children"),
    Input("page-3-graph-heatmap-per-sel", "hoverData"),
    Input("main-slider", "value"),
)
def page_3_hover(hoverData, slice_index):
    if hoverData is not None:
        if len(hoverData["points"]) > 0:
            x = int(slice_index) - 1
            z = hoverData["points"][0]["x"]
            y = hoverData["points"][0]["y"]

            slice_coor_rescaled = np.asarray(
                (atlas.array_coordinates_warped_data[x, y, z] * 1000 / atlas.resolution).round(0), dtype=np.int16,
            )
            try:
                label = atlas.labels[tuple(slice_coor_rescaled)]
            except:
                label = "undefined"
            return "Hovered region: " + label

    return dash.no_update


@app.app.callback(
    Output("page-3-graph-atlas-hover-text", "children"),
    Input("page-3-graph-atlas-per-sel", "hoverData"),
    Input("main-slider", "value"),
)
def page_3_atlas_hover(hoverData, slice_index):
    if hoverData is not None:
        if len(hoverData["points"]) > 0:
            x = int(slice_index) - 1
            z = hoverData["points"][0]["x"]
            y = hoverData["points"][0]["y"]

            slice_coor_rescaled = np.asarray(
                (atlas.array_coordinates_warped_data[x, y, z] * 1000 / atlas.resolution).round(0), dtype=np.int16,
            )
            try:
                label = atlas.labels[tuple(slice_coor_rescaled)]
            except:
                label = "undefined"
            return "Hovered region: " + label

    return dash.no_update


# Function to plot the initial heatmap
@app.app.callback(
    Output("page-3-graph-heatmap-per-sel", "relayoutData"),
    Input("page-3-reset-button", "n_clicks"),
    Input("url", "pathname"),
    prevent_initial_call=True,
)
def tab_3_reset_layout(cliked_reset, url):
    return {}


# Function to add clicked regions to selected options in dropdown
@app.app.callback(
    Output("page-3-dropdown-brain-regions", "value"),
    Input("main-slider", "value"),
    Input("page-3-reset-button", "n_clicks"),
    Input("url", "pathname"),
    Input("page-3-graph-atlas-per-sel", "clickData"),
    State("page-3-dropdown-brain-regions", "value"),
    prevent_initial_call=True,
)
def tab_3_add_value_dropdown(slice_index, clicked_reset, url, clickData, l_mask_names):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]
    if id_input == "main-slider" or len(id_input) == 0 or id_input == "page-3-reset-button" or id_input == "url":
        return []

    if clickData is not None:

        # no more than 4 annotations otherwise it's too heavy for the server
        if l_mask_names is not None:
            if len(l_mask_names) > 3:
                return dash.no_update

        if len(clickData["points"]) > 0:
            x = int(slice_index) - 1
            z = clickData["points"][0]["x"]
            y = clickData["points"][0]["y"]

            slice_coor_rescaled = np.asarray(
                (atlas.array_coordinates_warped_data[x, y, z] * 1000 / atlas.resolution).round(0), dtype=np.int16,
            )
            try:
                mask_name = label = atlas.labels[tuple(slice_coor_rescaled)]
                if l_mask_names is not None:
                    if mask_name in l_mask_names:
                        return dash.no_update
                    l_mask_names.append(mask_name)
                else:
                    l_mask_names = [mask_name]
                return l_mask_names
            except:
                logging.info("The coordinate is out of the ccfv3")

    return dash.no_update


# Function to plot the initial heatmap
@app.app.callback(
    Output("page-3-graph-heatmap-per-sel", "figure"),
    Output("dcc-store-color-mask", "data"),
    Output("dcc-store-reset", "data"),
    Output("dcc-store-shapes-and-masks", "data"),
    Input("page-3-graph-heatmap-per-sel", "relayoutData"),
    Input("main-slider", "value"),
    Input("page-3-reset-button", "n_clicks"),
    Input("page-3-dropdown-brain-regions", "value"),
    Input("url", "pathname"),
    State("dcc-store-color-mask", "data"),
    State("dcc-store-reset", "data"),
    State("dcc-store-shapes-and-masks", "data"),
    prevent_inital_call=True,
)
def page_3_plot_heatmap(
    relayoutData, slice_index, cliked_reset, l_mask_name, url, l_color_mask, reset, l_shapes_and_masks,
):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]

    # if value_input != "hoverData":
    #    print(id_input, value_input, slice_index, cliked_reset, l_mask_name, url, l_color_mask, reset)

    # If a new slice is loaded or the page just got loaded
    # do nothing because of automatic relayout of the heatmap which is automatically triggered when the page is loaded
    if id_input == "main-slider" or len(id_input) == 0 or id_input == "page-3-reset-button" or id_input == "url":
        fig = return_pickled_object(
            "figures/load_page",
            "figure_basic_image",
            force_update=False,
            compute_function=figures.compute_figure_basic_image,
            type_figure="projection_corrected",
            index_image=slice_index - 1,
            plot_atlas_contours=False,
        )
        fig.update_layout(
            dragmode="drawclosedpath",
            newshape=dict(fillcolor=config.l_colors[0], opacity=0.7, line=dict(color="white", width=1)),
            autosize=True,
        )
        return fig, [], True, []

    # fix bug
    if value_input == "relayoutData" and relayoutData == {"autosize": True}:
        return dash.no_update

    # fig other bug
    if (
        id_input == "page-3-dropdown-brain-regions "
        and relayoutData is None
        and cliked_reset is None
        and l_mask_name is None
    ):
        fig = return_pickled_object(
            "figures/load_page",
            "figure_basic_image",
            force_update=False,
            compute_function=figures.compute_figure_basic_image,
            type_figure="projection_corrected",
            index_image=slice_index - 1,
            plot_atlas_contours=False,
        )

        fig.update_layout(
            dragmode="drawclosedpath",
            newshape=dict(fillcolor=config.l_colors[0], opacity=0.7, line=dict(color="white", width=1)),
            autosize=True,
        )
        return fig, [], True, []

    if id_input == "page-3-graph-heatmap-per-sel" or id_input == "page-3-dropdown-brain-regions":
        # Rebuild figure
        fig = return_pickled_object(
            "figures/load_page",
            "figure_basic_image",
            force_update=False,
            compute_function=figures.compute_figure_basic_image,
            type_figure="projection_corrected",
            index_image=slice_index - 1,
            plot_atlas_contours=False,
        )
        color_idx = None
        col_next = None

        if l_mask_name is not None:

            if len(l_mask_name) > 0:
                dic_masks = return_pickled_object(
                    "atlas/atlas_objects",
                    "dic_masks_and_spectra",
                    force_update=False,
                    compute_function=atlas.compute_dic_projected_masks_and_spectra,
                    slice_index=slice_index - 1,
                )

                for idx_mask, mask_name in enumerate(l_mask_name):
                    if mask_name in dic_masks:
                        projected_mask = dic_masks[mask_name][0]

                    # Build a list of empty images and add selected lipids for each channel
                    normalized_projected_mask = projected_mask / np.max(projected_mask)
                    if idx_mask < len(l_color_mask):
                        color_rgb = l_color_mask[idx_mask]
                    else:
                        color_idx = len(l_color_mask)
                        if relayoutData is not None:
                            if "shapes" in relayoutData:
                                color_idx += len(relayoutData["shapes"])
                        color = config.l_colors[color_idx % 4][1:]
                        color_rgb = [int(color[i : i + 2], 16) for i in (0, 2, 4)] + [200]
                        l_color_mask.append(color_rgb)

                    l_images = [normalized_projected_mask * color for c, color in zip(["r", "g", "b", "a"], color_rgb)]
                    # Reoder axis to match plotly go.image requirements
                    array_image = np.moveaxis(np.array(l_images, dtype=np.uint8), 0, 2)

                    # convert image to string to save space (new image as each mask must have a different color)
                    base64_string = convert_image_to_base64(array_image, optimize=True, format="gif", type="RGBA")
                    fig.add_trace(go.Image(visible=True, source=base64_string, hoverinfo="skip"))
                    fig.update_layout(dragmode="drawclosedpath",)

                    if id_input == "page-3-dropdown-brain-regions" and color_idx is not None:
                        # save in l_shapes_and_masks
                        l_shapes_and_masks.append(["mask", mask_name, base64_string, color_idx])

        if relayoutData is not None:
            if "shapes" in relayoutData:
                if len(relayoutData["shapes"]) > 0:
                    if not reset or value_input == "relayoutData":
                        if "path" in relayoutData["shapes"][-1]:
                            fig["layout"]["shapes"] = relayoutData["shapes"]  #
                            # if color_idx is not None:
                            #    col_next = config.l_colors[(color_idx + 1) % 4]
                            # else:
                            col_next = config.l_colors[(len(relayoutData["shapes"]) + len(l_color_mask)) % 4]

                            # compute color and save in l_shapes_and_masks
                            if id_input == "page-3-graph-heatmap-per-sel":
                                color_idx_for_registration = len(l_color_mask)
                                if relayoutData is not None:
                                    if "shapes" in relayoutData:
                                        color_idx_for_registration += len(relayoutData["shapes"])
                                l_shapes_and_masks.append(
                                    ["shape", None, relayoutData["shapes"][-1], color_idx_for_registration - 1]
                                )

        if color_idx is not None and col_next is None:
            col_next = config.l_colors[(color_idx + 1) % 4]
        elif col_next is None:
            col_next = config.l_colors[0]
        fig.update_layout(
            dragmode="drawclosedpath",
            newshape=dict(fillcolor=col_next, opacity=0.7, line=dict(color="white", width=1),),
        )

        if relayoutData is not None:
            if "shapes" in relayoutData:
                if len(relayoutData["shapes"]) + len(l_color_mask) > 3:
                    fig.update_layout(dragmode=False)
        if len(l_color_mask) > 3:
            fig.update_layout(dragmode=False)

        return fig, l_color_mask, False, l_shapes_and_masks

    # either graph is already here
    return dash.no_update


# Function to plot the maks annotation on the initial heatmap
@app.app.callback(
    Output("page-3-graph-atlas-per-sel", "figure"),
    Output("page-3-dcc-store-basic-figure", "data"),
    Input("main-slider", "value"),
    Input("url", "pathname"),
    Input("page-3-graph-atlas-per-sel", "hoverData"),
    State("page-3-dcc-store-basic-figure", "data"),
    prevent_inital_call=True,
)
def page_3_plot_masks(slice_index, url, hoverData, basic_figure_plotted):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]

    # slider has been moved
    if id_input == "main-slider":
        return figures.dic_fig_contours[slice_index - 1], True

    # Get hover data
    if value_input == "hoverData":
        if hoverData is not None:
            if len(hoverData["points"]) > 0:
                x = int(slice_index) - 1
                z = hoverData["points"][0]["x"]
                y = hoverData["points"][0]["y"]

                slice_coor_rescaled = np.asarray(
                    (atlas.array_coordinates_warped_data[x, y, z] * 1000 / atlas.resolution).round(0), dtype=np.int16,
                )
                try:
                    # This line will trigger an exception if the coordinate doesn't exist
                    mask_name = atlas.labels[tuple(slice_coor_rescaled)]
                    exception = mask_name not in atlas.dic_mask_images[slice_index - 1]
                except:
                    logging.info("The coordinate doesn't belong to the ccfv3")
                    exception = True

                if exception:
                    if basic_figure_plotted:
                        return dash.no_update
                    else:
                        return figures.dic_fig_contours[slice_index - 1], True
                else:
                    im = atlas.dic_mask_images[slice_index - 1][mask_name]
                    fig = copy.copy(figures.dic_fig_contours[slice_index - 1])
                    fig.add_trace(im)
                    return fig, False

    return dash.no_update


# Function that activate the button to compute spectra
@app.app.callback(
    Output("page-3-button-compute-spectra", "disabled"),
    Input("page-3-graph-heatmap-per-sel", "relayoutData"),
    Input("page-3-reset-button", "n_clicks"),
    Input("page-3-dropdown-brain-regions", "value"),
)
def page_3_button_compute_spectra(relayoutData, clicked_reset, mask):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if id_input == "page-3-reset-button":
        return True

    if mask is not None:
        if mask != []:
            return False

    if relayoutData is not None:
        if "shapes" in relayoutData:
            if len(relayoutData["shapes"]) > 0:
                return False

    return True


# Function to make visible the m/z plot in tab 3
@app.app.callback(
    Output("page-3-graph-spectrum-per-pixel", "style"),
    Output("page-3-alert-2", "style"),
    Output("page-3-graph-heatmap-per-lipid", "style"),
    Output("page-3-div-dropdown", "style"),
    Input("page-3-reset-button", "n_clicks"),
    Input("page-3-button-compute-spectra", "n_clicks"),
    State("page-3-dropdown-brain-regions", "value"),
    State("page-3-graph-heatmap-per-sel", "relayoutData"),
)
def tab_3_display_high_res_mz_plot(clicked_reset, clicked_compute, mask, relayoutData):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if id_input == "page-3-reset-button":
        return {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}

    elif id_input == "page-3-button-compute-spectra":
        logging.info("Compute spectra button has been clicked")

        if mask is not None:
            if mask != []:
                logging.info("One or several masks have been selected, displaying graphs")
                return {"height": HEIGHT_PLOTS}, {"display": "none"}, {"height": 2 * HEIGHT_PLOTS}, {}

        if relayoutData is not None:
            if "shapes" in relayoutData:
                if len(relayoutData["shapes"]) > 0:
                    if len(relayoutData["shapes"]) <= 4:
                        logging.info("One or several shapes have been selected, displaying graphs")
                        return {"height": HEIGHT_PLOTS}, {"display": "none"}, {"height": 2 * HEIGHT_PLOTS}, {}
                    else:
                        return {"display": "none"}, {}, {"display": "none"}, {"display": "none"}

    return dash.no_update


# Function to make visible the sorting switch for the lipid heatmap
@app.app.callback(
    Output("page-3-switches", "className"),
    # Input("page-3-button-compute-spectra", "n_clicks"),
    Input("page-3-reset-button", "n_clicks"),
    Input("page-3-graph-heatmap-per-lipid", "figure"),
    State("page-3-graph-heatmap-per-sel", "relayoutData"),
)
def page_3_display_switch(clicked_reset, fig_heatmap, relayoutData):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if id_input == "page-3-reset-button":
        return "d-none"

    # elif id_input == "page-3-button-compute-spectra":

    # If limit number of selection is done, just hide it
    if relayoutData is not None:
        if "shapes" in relayoutData:
            if len(relayoutData["shapes"]) > 0:
                if len(relayoutData["shapes"]) > 4:
                    return "d-none"

    if fig_heatmap is not None:
        if len(fig_heatmap["data"]) > 0:

            # If more than 1 selection recorded in the heatmap, display switch
            if len(fig_heatmap["data"][0]["x"]) > 1:
                return "ml-1 d-flex align-items-center justify-content-center"
            else:
                return "d-none"

    return dash.no_update


# Function to make visible the alert regarding the m/z plot in tab 3
@app.app.callback(
    Output("page-3-alert", "style"),
    Output("page-3-alert-3", "style"),
    Output("page-3-alert-4", "style"),
    Output("page-3-alert-5", "style"),
    Input("page-3-button-compute-spectra", "n_clicks"),
    Input("page-3-reset-button", "n_clicks"),
    State("page-3-graph-heatmap-per-sel", "relayoutData"),
    State("page-3-dropdown-brain-regions", "value"),
)
def page_3_display_alert(clicked_compute, clicked_reset, relayoutData, mask):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if id_input == "page-3-reset-button":
        return {}, {}, {}, {}

    elif id_input == "page-3-button-compute-spectra":
        if mask is not None:
            if mask != []:
                return {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}

        if relayoutData is not None:
            if "shapes" in relayoutData:
                if len(relayoutData["shapes"]) > 0:
                    return {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}
    return dash.no_update


# Function to compute path when heatmap has been annotated
@app.app.callback(
    Output("page-3-dcc-store-path-heatmap", "data"),
    Output("page-3-dcc-store-loading-1", "data"),
    Input("page-3-button-compute-spectra", "n_clicks"),
    Input("page-3-reset-button", "n_clicks"),
    Input("url", "pathname"),
    State("page-3-graph-heatmap-per-sel", "relayoutData"),
    Input("main-slider", "value"),
    prevent_initial_call=True,
)
def page_3_load_path(clicked_compute, cliked_reset, url, relayoutData, slice_index):

    # Most likely, we will only work with the projected data from now on
    PROJECT_IMAGE = True

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]

    # If a new slice is loaded or the page just got loaded, do nothing because
    # of automatic relayout of the heatmap which is automatically triggered when the page is loaded
    if len(id_input) == 0:
        return dash.no_update

    if value_input == "relayoutData" and relayoutData == {"autosize": True}:
        return dash.no_update

    # If the figure has been reset
    if id_input == "page-3-reset-button" or id_input == "url":
        return [], False

    if id_input == "page-3-button-compute-spectra":

        # If an annotation has been drawn, compute the average spectrum in the annotation
        if relayoutData is not None:
            if "shapes" in relayoutData:
                if len(relayoutData["shapes"]) > 0 and len(relayoutData["shapes"]) <= 4:
                    logging.info("Starting to compute path")
                    l_paths = []
                    for shape in relayoutData["shapes"]:
                        if "path" in shape:
                            # get condensed path version of the annotation
                            parsed_path = shape["path"][1:-1].replace("L", ",").split(",")
                            path = [round(float(x)) for x in parsed_path]

                            if PROJECT_IMAGE:
                                path = [
                                    (
                                        int(
                                            atlas.array_projection_correspondence_corrected[slice_index - 1, y, x, 0]
                                        ),  # must explicitely cast to int for serialization as numpy int are not accepted
                                        int(atlas.array_projection_correspondence_corrected[slice_index - 1, y, x, 1]),
                                    )
                                    for x, y in zip(path[:-1:2], path[1::2])
                                ]
                                # clean path from artefacts due to projection
                                path = [
                                    t for t in list(dict.fromkeys(path)) if -1 not in t
                                ]  # use dic key to remove duplicates created by the correction of the projection
                            else:
                                path = [(y, x) for x, y in zip(path[:-1:2], path[1::2])]
                            if len(path) > 0:
                                path.append(path[0])  # to close the path
                            l_paths.append(path)

                    logging.info("Returning path")
                    return l_paths, True

    return dash.no_update


# Function that takes path or mask and compute corresponding spectrum
@app.app.callback(
    Output("dcc-store-list-mz-spectra", "data"),
    Output("page-3-dcc-store-loading-2", "data"),
    Input("page-3-button-compute-spectra", "n_clicks"),
    Input("page-3-dcc-store-path-heatmap", "data"),
    Input("page-3-reset-button", "n_clicks"),
    Input("url", "pathname"),
    State("page-3-dropdown-brain-regions", "value"),
    Input("main-slider", "value"),
    State("dcc-store-list-mz-spectra", "data"),
    State("dcc-store-shapes-and-masks", "data"),
    State("page-3-normalize", "value"),
    State("page-3-log", "value"),
    prevent_intial_call=True,
)
def page_3_record_spectra(
    clicked_compute,
    l_paths,
    cliked_reset,
    url,
    l_mask_name,
    slice_index,
    l_spectra,
    l_shapes_and_masks,
    as_enrichment,
    log_transform,
):
    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]

    # print(id_input, value_input, path, cliked_reset, l_mask_name, slice_index)
    # If a new slice is loaded or the page just got loaded, do nothing
    if len(id_input) == 0:
        return [], False

    # Delete everything when clicking reset
    elif id_input == "page-3-reset-button" or id_input == "url":
        return [], False

    elif id_input == "page-3-button-compute-spectra":
        logging.info("Starting to compute spectrum")
        l_spectra = []
        idx_mask = -1
        idx_path = -1
        for shape in l_shapes_and_masks:
            grah_scattergl_data = None
            # Compute average spectrum from mask
            if shape[0] == "mask":
                idx_mask += 1
                try:
                    mask_name = l_mask_name[idx_mask]
                    dic_masks = return_pickled_object(
                        "atlas/atlas_objects",
                        "dic_masks_and_spectra",
                        force_update=False,
                        compute_function=atlas.compute_dic_projected_masks_and_spectra,
                        slice_index=slice_index - 1,
                    )
                    if mask_name in dic_masks:
                        grah_scattergl_data = dic_masks[mask_name][1]
                except:
                    logging.warning("Bug, the selected mask does't exist")
                    return dash.no_update
            elif shape[0] == "shape":
                idx_path += 1
                try:
                    path = l_paths[idx_path]
                    if len(path) > 0:
                        list_index_bound_rows, list_index_bound_column_per_row = sample_rows_from_path(
                            np.array(path, dtype=np.int32)
                        )
                        # print("from selection", list_index_bound_rows, list_index_bound_column_per_row)

                        grah_scattergl_data = compute_spectrum_per_row_selection(
                            list_index_bound_rows,
                            list_index_bound_column_per_row,
                            data.get_array_spectra(slice_index),
                            data.get_array_lookup_pixels(slice_index),
                            data.get_image_shape(slice_index),
                            zeros_extend=False,
                        )
                except:
                    logging.warning("Bug, the selected path does't exist")
                    return dash.no_update
            else:
                logging.warning("Bug, the shape type doesn't exit")

            # Do the selected transformations
            if grah_scattergl_data is not None:
                if as_enrichment:
                    # first normalize with respect to itself
                    grah_scattergl_data[1, :] /= np.sum(grah_scattergl_data[1, :])

                    # then convert to uncompressed version
                    grah_scattergl_data = convert_array_to_fine_grained(grah_scattergl_data, 10 ** -3, lb=350, hb=1250)

                    # then normalize to the sum of all pixels
                    grah_scattergl_data[1, :] /= (
                        convert_array_to_fine_grained(
                            data.get_array_spectra(slice_index - 1), 10 ** -3, lb=350, hb=1250,
                        )[1, :]
                        + 1
                    )

                    # go back to compressed
                    grah_scattergl_data = strip_zeros(grah_scattergl_data)

                    # re-normalize with respect to the number of values in the spectrum
                    # so that pixels with more lipids do no have lower peaks
                    grah_scattergl_data[1, :] *= len(grah_scattergl_data[1, :])

                # log-transform
                if log_transform:
                    grah_scattergl_data[1, :] = np.log(grah_scattergl_data[1, :] + 1)
                l_spectra.append(grah_scattergl_data)

        if l_spectra != []:
            logging.info("Spectra computed, returning it now")
            return l_spectra, True

    return [], False


# Function that takes path and plot spectrum
@app.app.callback(
    Output("page-3-graph-spectrum-per-pixel", "figure"),
    # Output("page-3-graph-heatmap-per-lipid-wait", "children"),  # second (empty) output to synchronize graphs spinners
    # Output("page-3-div-dropdown-wait", "children"),  # third(empty) output to synchronize graphs spinners
    # Output("page-3-graph-lipid--comparison-wait", "children"),
    Output("dcc-store-list-idx-lipids", "data"),
    Output("page-3-dcc-store-loading-3", "data"),
    Input("page-3-reset-button", "n_clicks"),
    Input("dcc-store-list-mz-spectra", "data"),
    Input("main-slider", "value"),
    prevent_intial_call=True,
)
def page_3_plot_spectrum(cliked_reset, l_spectra, slice_index):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]

    # If a new slice is loaded or the page just got loaded, do nothing
    if len(id_input) == 0:
        return dash.no_update

    # Delete everything when clicking reset
    elif id_input == "page-3-reset-button" or l_spectra is None:
        return figures.return_empty_spectrum(), [], False

    # do nothing if l_spectra is None or []
    elif id_input == "dcc-store-list-mz-spectra":
        if len(l_spectra) > 0:
            logging.info("Starting spectra plotting now")
            fig_mz = go.Figure()
            ll_idx_labels = []

            for idx_spectra, spectrum in enumerate(l_spectra):

                col = config.l_colors[idx_spectra % 4]

                # Get the average spectrum and add it to m/z plot
                grah_scattergl_data = np.array(spectrum, dtype=np.float32)

                # Get df for current slice
                df_names = data.get_annotations()[data.get_annotations()["slice"] == slice_index]

                # Extract lipid names
                l_idx_labels = return_index_labels(
                    df_names["min"].to_numpy(), df_names["max"].to_numpy(), grah_scattergl_data[0, :],
                )

                # It's ok to do two loops since l_idx_labels is relatively small
                l_idx_kept = [i for i, x in enumerate(l_idx_labels) if x >= 0]
                l_idx_unkept = [i for i, x in enumerate(l_idx_labels) if x < 0]

                # Pad annotated trace with zeros
                (grah_scattergl_data_padded_annotated, array_index_padding,) = add_zeros_to_spectrum(
                    grah_scattergl_data[:, l_idx_kept], pad_individual_peaks=True, padding=10 ** -4,
                )
                l_mz_with_lipids = grah_scattergl_data_padded_annotated[0, :]
                l_intensity_with_lipids = grah_scattergl_data_padded_annotated[1, :]
                l_idx_labels_kept = l_idx_labels[l_idx_kept]

                ll_idx_labels.append(l_idx_labels)

                # @njit #we need to wait for the support of np.insert
                def pad_l_idx_labels(l_idx_labels_kept, array_index_padding):
                    pad = 0
                    # The initial condition in the loop is only evaluated once so no problem with insertion afterwards
                    for i in range(len(l_idx_labels_kept)):
                        # Array_index_padding[i] will be 0 or 2 (peaks are padded with 2 zeros, one on each side)
                        for j in range(array_index_padding[i]):
                            # i+1 instead of i plus insert on the right of the element i
                            l_idx_labels_kept = np.insert(l_idx_labels_kept, i + 1 + pad, -1)
                            pad += 1
                    return l_idx_labels_kept

                l_idx_labels_kept = list(pad_l_idx_labels(l_idx_labels_kept, array_index_padding))

                # Rebuild lipid name from structure, cation, etc.
                l_labels = [
                    df_names.iloc[idx]["name"]
                    + "_"
                    + df_names.iloc[idx]["structure"]
                    + "_"
                    + df_names.iloc[idx]["cation"]
                    if idx != -1
                    else ""
                    for idx in l_idx_labels_kept
                ]

                # Add annotated trace to plot
                fig_mz.add_trace(
                    go.Scattergl(
                        x=l_mz_with_lipids,
                        y=l_intensity_with_lipids,
                        visible=True,
                        marker_color=col,
                        name="Annotated peaks",
                        showlegend=True,
                        fill="tozeroy",
                        hovertemplate="Lipid: %{text}<extra></extra>",
                        text=l_labels,
                    )
                )

                # Pad not annotated traces peaks with zeros
                grah_scattergl_data_padded, array_index_padding = add_zeros_to_spectrum(
                    grah_scattergl_data[:, l_idx_unkept], pad_individual_peaks=True, padding=10 ** -4,
                )
                l_mz_without_lipids = grah_scattergl_data_padded[0, :]
                l_intensity_without_lipids = grah_scattergl_data_padded[1, :]

                # Add not-annotated trace to plot.
                fig_mz.add_trace(
                    go.Scattergl(
                        x=l_mz_without_lipids,
                        y=l_intensity_without_lipids,
                        visible=True,
                        marker_color=col,
                        name="Unknown peaks",
                        showlegend=True,
                        fill="tozeroy",
                        opacity=0.2,
                        hoverinfo="skip",
                        # text=l_idx_labels_kept,
                    )
                )
            # Define figure layout
            fig_mz.update_layout(
                margin=dict(t=5, r=0, b=10, l=0),
                showlegend=True,
                xaxis=dict(title="m/z"),
                yaxis=dict(title="Intensity"),
                template="plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.1),
            )

            logging.info("Spectra plotted. Returning it now")
            return fig_mz, ll_idx_labels, True

    return dash.no_update


# Function that plots heatmap representing lipid intensity from the current selection
@app.app.callback(
    Output("page-3-graph-heatmap-per-lipid", "figure"),
    Output("page-3-dcc-store-lipids-region", "data"),
    # Output("page-3-graph-spectrum-per-pixel-wait", "children"),  # empty output to synchronize graphs spinners
    Output("page-3-dcc-store-loading-4", "data"),
    Input("dcc-store-list-idx-lipids", "data"),
    Input("page-3-reset-button", "n_clicks"),
    Input("page-3-sort-by-diff-switch", "value"),
    # Input("page-3-scale-by-mean-switch", "value"),
    Input("page-4-slider", "value"),
    State("dcc-store-list-mz-spectra", "data"),
    Input("main-slider", "value"),
    prevent_intial_call=True,
)
def page_3_draw_heatmap_per_lipid_selection(
    ll_idx_labels, cliked_reset, sort_switch, percentile, l_spectra, slice_index
):
    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]

    # If a new slice is loaded or the page just got loaded, do nothing
    if len(id_input) == 0:
        return dash.no_update

    # Delete everything when clicking reset
    elif id_input == "page-3-reset-button":
        return figures.return_heatmap_lipid(), [], False

    # Otherwise compute lipid expression heatmap from spectrum
    elif (
        id_input == "dcc-store-list-idx-lipids"
        or id_input == "page-3-sort-by-diff-switch"
        or id_input == "page-3-scale-by-mean-switch"
        or id_input == "page-4-slider"
    ):

        logging.info("Starting computing heatmap now")

        # Correct for selector values
        if len(sort_switch) > 0:
            sort_switch = sort_switch[0]
        else:
            sort_switch = False

        # if len(scale_switch) > 0:
        #    scale_switch = scale_switch[0]
        # else:
        #    scale_switch = False
        scale_switch = False

        # Load figure
        if l_spectra is not None and ll_idx_labels is not None:
            if len(l_spectra) > 0:
                if len(ll_idx_labels) != len(l_spectra):
                    print("BUG: the number of received spectra is different from the number of received annotations")
                    return dash.no_update

                # Compute average expression for each lipid and each selection
                set_lipids_idx = set()
                ll_lipids_idx = []
                ll_avg_intensity = []
                n_sel = len(l_spectra)
                for spectrum, l_idx_labels in zip(l_spectra, ll_idx_labels):

                    array_intensity_with_lipids = np.array(spectrum, dtype=np.float32)[1, :]
                    array_idx_labels = np.array(l_idx_labels, dtype=np.int32)
                    l_lipids_idx, l_avg_intensity = compute_avg_intensity_per_lipid(
                        array_intensity_with_lipids, array_idx_labels
                    )
                    set_lipids_idx.update(l_lipids_idx)
                    ll_lipids_idx.append(l_lipids_idx)
                    ll_avg_intensity.append(l_avg_intensity)

                dic_avg_lipids = {idx: [0] * n_sel for idx in set_lipids_idx}
                for i, (l_lipids, l_avg_intensity) in enumerate(zip(ll_lipids_idx, ll_avg_intensity)):
                    for lipid, intensity in zip(l_lipids, l_avg_intensity):
                        dic_avg_lipids[lipid][i] = intensity

                l_sel = ["Blue sel.", "Green sel.", "Orange sel.", "Red sel."]
                df_avg_intensity_lipids = pd.DataFrame.from_dict(
                    dic_avg_lipids, orient="index", columns=[l_sel[i] for i in range(n_sel)]
                )

                # Exclude very lowly expressed lipids
                df_min_expression = df_avg_intensity_lipids.min(axis=1)
                df_avg_intensity_lipids = df_avg_intensity_lipids[
                    df_min_expression > df_min_expression.quantile(q=int(percentile) / 100)
                ]

                # Rescale according to row mean
                if scale_switch and n_sel > 1:
                    df_avg_intensity_lipids = df_avg_intensity_lipids.divide(
                        df_avg_intensity_lipids.mean(axis=1), axis=0
                    )

                # Sort by relative std
                if sort_switch and n_sel > 1:
                    df_avg_intensity_lipids = df_avg_intensity_lipids.iloc[
                        (df_avg_intensity_lipids.std(axis=1) / df_avg_intensity_lipids.mean(axis=1)).argsort(), :
                    ]
                else:
                    # df_avg_intensity_lipids.sort_index(ascending=False, inplace=True)
                    if n_sel > 1:
                        df_avg_intensity_lipids = df_avg_intensity_lipids.iloc[
                            (df_avg_intensity_lipids.mean(axis=1)).argsort(), :
                        ]
                    else:
                        df_avg_intensity_lipids.sort_values(by=l_sel[0], inplace=True)

                l_idx_lipids = list(df_avg_intensity_lipids.index)

                # Replace idx_lipids by actual name
                df_names = data.get_annotations()[data.get_annotations()["slice"] == slice_index]
                df_avg_intensity_lipids.index = df_avg_intensity_lipids.index.map(
                    lambda idx: df_names.iloc[idx]["name"]
                    + "_"
                    + df_names.iloc[idx]["structure"]
                    + "_"
                    + df_names.iloc[idx]["cation"]
                )

                # Plot
                fig_heatmap_lipids = go.Figure(
                    data=go.Heatmap(
                        z=df_avg_intensity_lipids.to_numpy(),
                        y=df_avg_intensity_lipids.index,
                        x=df_avg_intensity_lipids.columns,
                        ygap=0.2,
                        colorscale="Blues",
                    )
                )
                fig_heatmap_lipids = figures.return_heatmap_lipid(fig_heatmap_lipids)

                logging.info("Heatmap computed. Returning it now")
                return fig_heatmap_lipids, l_idx_lipids, True

    return dash.no_update


# Function that sends the spectra of the selected region for download
@app.app.callback(
    Output("tab-3-download-data", "data"),
    Input("tab-3-download-data-button", "n_clicks"),
    State("page-3-graph-spectrum-per-pixel", "figure"),
    prevent_initial_call=True,
)
def tab_3_download(n_clicks, fig_mz):
    if fig_mz is not None:
        fig_mz = go.Figure(data=fig_mz)
        if len(fig_mz.data) > 1:

            # Excel writer for download
            def to_excel(bytes_io):
                xlsx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
                for i, data in enumerate(fig_mz.data):
                    if i % 2 == 0:
                        df = pd.DataFrame.from_dict({"m/z": data["x"], "Intensity": data["y"], "Lipid": data["text"],})
                        df.to_excel(
                            xlsx_writer, index=False, sheet_name="Annotated spectrum sel " + str(i // 2 + 1),
                        )
                    else:
                        df = pd.DataFrame.from_dict({"m/z": data["x"], "Intensity": data["y"]})
                        df.to_excel(
                            xlsx_writer, index=False, sheet_name="Remaining spectrum sel " + str(i // 2 + 1),
                        )
                xlsx_writer.save()

            return dcc.send_data_frame(to_excel, "my_region_selection.xlsx")

    return dash.no_update


# Function that deactivate the download button if not region drawn
@app.app.callback(
    Output("tab-3-download-data-button", "disabled"), Input("page-3-graph-spectrum-per-pixel", "figure"),
)
def page_3_reset_download(fig_mz):
    if fig_mz is not None:
        fig_mz = go.Figure(data=fig_mz)
        if len(fig_mz.data) > 1:
            return False
    return True


# Function that create the dropdown lipids selections
@app.app.callback(
    Output("page-3-dropdown-red", "options"),
    Output("page-3-dropdown-green", "options"),
    Output("page-3-dropdown-blue", "options"),
    Output("page-3-dropdown-red", "value"),
    Output("page-3-dropdown-green", "value"),
    Output("page-3-dropdown-blue", "value"),
    Output("page-3-open-modal", "n_clicks"),
    Input("page-3-dcc-store-lipids-region", "data"),
    Input("page-3-reset-button", "n_clicks"),
    Input("main-slider", "value"),
    State("page-3-open-modal", "n_clicks"),
)
def page_3_fill_dropdown_options(l_idx_lipids, cliked_reset, slice_index, n_clicks):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]

    # If a new slice is loaded or the page just got loaded, do nothing
    if len(id_input) == 0:
        return dash.no_update

    # Delete everything when clicking reset
    elif id_input == "page-3-reset-button":
        return [], [], [], [], [], [], None

    # Otherwise compute lipid expression heatmap from spectrum
    elif id_input == "page-3-dcc-store-lipids-region":
        if l_idx_lipids is not None:
            if len(l_idx_lipids) > 0:
                logging.info("Starting computing lipid dropdown now.")
                df_names = data.get_annotations()[data.get_annotations()["slice"] == slice_index]
                l_names = [
                    df_names.iloc[idx]["name"]
                    + "_"
                    + df_names.iloc[idx]["structure"]
                    + "_"
                    + df_names.iloc[idx]["cation"]
                    for idx in l_idx_lipids
                ]
                options = [{"label": name, "value": idx} for name, idx in zip(l_names, l_idx_lipids)]

                # dropdown is displayed in reversed order
                options.reverse()

                if n_clicks is None:
                    n_clicks = 0
                if len(options) > 0:
                    logging.info("Dropdown values computed. Updating it with new lipids now.")
                    return (
                        options,
                        options,
                        options,
                        [options[0]["value"]],
                        [options[1]["value"]],
                        [options[2]["value"]],
                        n_clicks + 1,
                    )

    return dash.no_update


# Function that activate the button to plot the graph for lipid comparison
@app.app.callback(
    Output("page-3-open-modal", "disabled"),
    Input("page-3-dropdown-red", "value"),
    Input("page-3-dropdown-green", "value"),
    Input("page-3-dropdown-blue", "value"),
)
def toggle_button_modal(l_red_lipids, l_green_lipids, l_blue_lipids):
    # Check that at least one lipid has been selected
    if len(l_red_lipids + l_green_lipids + l_blue_lipids) > 0:
        return False
    else:
        return True


# Function that display the graph for lipid comparison
@app.app.callback(
    Output("page-3-div-graph-lipid-comparison", "style"),
    Input("page-3-open-modal", "n_clicks"),
    Input("page-3-reset-button", "n_clicks"),
    State("page-3-dropdown-red", "value"),
    State("page-3-dropdown-green", "value"),
    State("page-3-dropdown-blue", "value"),
)
def toggle_visibility_graph(n1, cliked_reset, l_red_lipids, l_green_lipids, l_blue_lipids):
    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    # Delete everything when clicking reset
    if id_input == "page-3-reset-button":
        return {"display": "none"}

    # Check that at least one lipid has been selected
    if len(l_red_lipids + l_green_lipids + l_blue_lipids) > 0:
        return {}
    else:
        return {"display": "none"}


# Function that draws modal graph according to selected lipids
@app.app.callback(
    Output("page-3-heatmap-lipid-comparison", "figure"),
    Output("page-3-dcc-store-loading-5", "data"),
    Input("page-3-open-modal", "n_clicks"),
    Input("page-3-reset-button", "n_clicks"),
    Input("page-3-toggle-mask", "value"),
    Input("main-slider", "value"),
    State("page-3-dropdown-red", "value"),
    State("page-3-dropdown-green", "value"),
    State("page-3-dropdown-blue", "value"),
    State("dcc-store-shapes-and-masks", "data"),
    State("page-3-dropdown-brain-regions", "value"),
    State("dcc-store-color-mask", "data"),
    State("page-3-log", "value"),
    State("page-3-normalize", "value"),
)
def draw_modal_graph(
    n1,
    cliked_reset,
    boolean_mask,
    slice_index,
    l_red_lipids,
    l_green_lipids,
    l_blue_lipids,
    l_shapes_and_masks,
    l_mask_name,
    l_color_mask,
    log,
    enrichment,
):
    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    logging.info("Modal graph function triggered with input " + str(id_input))

    # Delete everything when clicking reset or changing slice index
    if id_input == "page-3-reset-button" or id_input == "main-slider":
        logging.info("Resetting modal graph")
        return figures.return_empty_spectrum(), False

    # Check that at least one lipid has been selected
    if len(l_red_lipids + l_green_lipids + l_blue_lipids) > 0:
        logging.info("At least one lipid has been selected, starting computing modal graph now.")
        df_names = data.get_annotations()[data.get_annotations()["slice"] == slice_index]
        # Build the list of mz boundaries for each peak
        l_lipid_bounds = [
            [
                (float(df_names.iloc[index]["min"]), float(df_names.iloc[index]["max"]),) if index != -1 else None
                for index in l_lipids
            ]
            for l_lipids in [l_red_lipids, l_green_lipids, l_blue_lipids]
        ]

        fig = figures.compute_rgb_image_per_lipid_selection(
            slice_index, l_lipid_bounds, title=False, enrichment=enrichment, log=log
        )
        if boolean_mask:
            if l_shapes_and_masks is not None:
                l_draw = []
                for shape in l_shapes_and_masks:
                    if shape[0] == "mask":
                        base64_string = shape[2]
                        fig.add_trace(go.Image(visible=True, source=base64_string, hoverinfo="skip"))
                    elif shape[0] == "shape":
                        draw = shape[2]
                        l_draw.append(draw)

                fig["layout"]["shapes"] = tuple(l_draw)
                # else:
                #    fig["layout"]["shapes"] = tuple(list(fig["layout"]["shapes"]).append(draw))
        logging.info("Modal graph computed. Returning it now")
        return fig, True

    logging.info("No lipid were selected, ignoring update.")
    return dash.no_update


# Function that handle loading bar
@app.app.callback(
    Output("page-3-progress", "value"),
    Input("page-3-dcc-store-loading-1", "data"),
    Input("page-3-dcc-store-loading-2", "data"),
    Input("page-3-dcc-store-loading-3", "data"),
    State("page-3-dcc-store-loading-4", "data"),
    Input("page-3-dcc-store-loading-5", "data"),
)
# * CAREFUL: loading-4 is a state now
def update_loading_bar(state_1, state_2, state_3, state_4, state_5):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    print(id_input, state_1, state_2, state_3, state_4, state_5)

    if id_input == "page-3-dcc-store-loading-1" and state_1:
        return 40
    if id_input == "page-3-dcc-store-loading-2" and state_2:
        return 50
    if id_input == "page-3-dcc-store-loading-3" and state_3:
        return 60
    if id_input == "page-3-dcc-store-loading-4" and state_4:
        return 70
    if id_input == "page-3-dcc-store-loading-5" and state_5:
        return 100

    return 0


# Function that handles loading bar and row visibility
@app.app.callback(
    Output("page-3-row-main-computations", "className"),
    Output("page-3-progress", "className"),
    Input("page-3-progress", "value"),
    Input("page-3-reset-button", "n_clicks"),
    Input("page-3-button-compute-spectra", "n_clicks"),
)
def update_loading_visibility(value, clicked_reset, clicked_compute):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if id_input == "page-3-progress" and value == 100:
        return "", "d-none"
    elif id_input == "page-3-button-compute-spectra":
        return "d-none", "mt-1"
    else:
        return "d-none", "mt-1"

