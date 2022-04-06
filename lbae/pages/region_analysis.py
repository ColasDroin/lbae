###### IMPORT MODULES ######

# Standard modules
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import logging
import dash_draggable
from numba import njit
import dash_mantine_components as dmc

# LBAE modules
import app
from app import figures, data, atlas, cache_flask
import config
from modules.tools.misc import return_shelved_object, convert_image_to_base64
from modules.tools.spectra import (
    sample_rows_from_path,
    compute_spectrum_per_row_selection,
    convert_array_to_fine_grained,
    strip_zeros,
    add_zeros_to_spectrum,
    compute_avg_intensity_per_lipid,
    global_lipid_index_store,
)

HEIGHT_PLOTS = 300
N_LINES = int(np.ceil(HEIGHT_PLOTS / 30))

###### DEFFINE PAGE LAYOUT ######

# ! This page is very slow even at first loading, so probably so automatic callbacks are triggered... Investigate that
# ! With throttling tool from Chrome


def return_layout(basic_config, slice_index=1):

    page = html.Div(
        style={
            "position": "absolute",
            "top": "0px",
            "right": "0px",
            "bottom": "0px",
            "left": "6rem",
            "background-color": "#1d1c1f",
            "overflow": "hidden",
        },
        children=[
            html.Div(
                className="page-1-fixed-aspect-ratio",
                style={"background-color": "#1d1c1f",},
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
                            "width": "95%",
                            "height": "95%",
                            "position": "absolute",
                            "left": "2.5%",
                            # "max-height": "40vh",
                        },
                        figure=return_shelved_object(
                            "figures/load_page",
                            "figure_basic_image",
                            force_update=False,
                            compute_function=figures.compute_figure_basic_image,
                            type_figure="projection_corrected",
                            index_image=slice_index - 1,
                            plot_atlas_contours=False,
                            draw=True,
                        ),
                    ),
                    dmc.Text(
                        "Hovered region: ",
                        id="page-3-graph-hover-text",
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
                    dmc.Group(
                        direction="column",
                        spacing=0,
                        style={"left": "1%", "top": "1em",},
                        class_name="position-absolute",
                        children=[
                            html.Div(children=" Structure selection", className="fs-5 text-light",),
                            dmc.Group(
                                spacing="xs",
                                align="flex-start",
                                children=[
                                    dmc.MultiSelect(
                                        id="page-3-dropdown-brain-regions",
                                        data=[
                                            {
                                                "label": atlas.dic_acronym_name[node],
                                                "value": atlas.dic_acronym_name[node],
                                            }
                                            for node in atlas.dic_existing_masks[slice_index - 1]
                                        ],
                                        searchable=True,
                                        nothingFound="No structure found",
                                        radius="md",
                                        size="xs",
                                        # variant="filled",
                                        placeholder="Choose brain structure",
                                        clearable=False,
                                        maxSelectedValues=3,
                                        transitionDuration=150,
                                        transition="pop-top-left",
                                        transitionTimingFunction="ease",
                                        style={"width": "20em",},
                                    ),
                                    dmc.Button(
                                        children="Compute spectra",
                                        id="page-3-button-compute-spectra",
                                        variant="filled",
                                        color="gray",
                                        radius="md",
                                        size="xs",
                                        disabled=True,
                                        compact=False,
                                        loading=False,
                                    ),
                                    dmc.Button(
                                        children="Reset",
                                        id="page-3-reset-button",
                                        variant="filled",
                                        color="gray",
                                        radius="md",
                                        size="xs",
                                        disabled=False,
                                        compact=False,
                                        loading=False,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                children=[
                    dbc.Offcanvas(
                        id="page-4-drawer-region-selection",
                        backdrop=False,
                        placement="end",
                        style={
                            "width": "calc(100% - 6rem)",
                            "height": "100%",
                            "background-color": "#1d1c1f",
                        },
                        children=[
                            dash_draggable.ResponsiveGridLayout(
                                id="draggable",
                                clearSavedLayout=True,
                                isDraggable=False,
                                isResizable=False,
                                containerPadding=[2, 2],
                                breakpoints={
                                    "xxl": 1600,
                                    "lg": 1200,
                                    "md": 996,
                                    "sm": 768,
                                    "xs": 480,
                                    "xxs": 0,
                                },
                                gridCols={
                                    "xxl": 12,
                                    "lg": 12,
                                    "md": 10,
                                    "sm": 6,
                                    "xs": 4,
                                    "xxs": 2,
                                },
                                layouts={
                                    # x sets the lateral position, y the vertical one, w is in columns (whose size depends on the dimension), h is in rows (30px)
                                    # nb columns go 12->12->10->6->4->2
                                    "xxl": [
                                        {
                                            "i": "page-3-card-spectrum",
                                            "x": 2,
                                            "y": 2,
                                            "w": 8,
                                            "h": N_LINES,
                                        },
                                        {
                                            "i": "page-3-card-heatmap",
                                            "x": 2,
                                            "y": 17,
                                            "w": 4,
                                            "h": 2 * N_LINES,
                                        },
                                        {
                                            "i": "page-3-card-graph-lipid-comparison",
                                            "x": 6,
                                            "y": 17,
                                            "w": 4,
                                            "h": 2 * N_LINES + 3,
                                        },
                                    ],
                                    "lg": [
                                        {
                                            "i": "page-3-card-spectrum",
                                            "x": 0,
                                            "y": 2,
                                            "w": 12,
                                            "h": N_LINES,
                                        },
                                        {
                                            "i": "page-3-card-heatmap",
                                            "x": 0,
                                            "y": 17,
                                            "w": 6,
                                            "h": 2 * N_LINES,
                                        },
                                        {
                                            "i": "page-3-card-graph-lipid-comparison",
                                            "x": 6,
                                            "y": 17,
                                            "w": 6,
                                            "h": 2 * N_LINES,
                                        },
                                    ],
                                    "md": [
                                        {
                                            "i": "page-3-card-spectrum",
                                            "x": 0,
                                            "y": 2,
                                            "w": 10,
                                            "h": N_LINES,
                                        },
                                        {
                                            "i": "page-3-card-heatmap",
                                            "x": 0,
                                            "y": 17,
                                            "w": 5,
                                            "h": 2 * N_LINES - 2,
                                        },
                                        {
                                            "i": "page-3-card-graph-lipid-comparison",
                                            "x": 5,
                                            "y": 17,
                                            "w": 5,
                                            "h": 2 * N_LINES - 2,
                                        },
                                    ],
                                    "sm": [
                                        {
                                            "i": "page-3-card-spectrum",
                                            "x": 0,
                                            "y": 2,
                                            "w": 6,
                                            "h": N_LINES,
                                        },
                                        {
                                            "i": "page-3-card-heatmap",
                                            "x": 0,
                                            "y": 19 + 7 + 5,
                                            "w": 6,
                                            "h": 2 * N_LINES - 2,
                                        },
                                        {
                                            "i": "page-3-card-graph-lipid-comparison",
                                            "x": 0,
                                            "y": 19 + 7 + 5 + N_LINES,
                                            "w": 6,
                                            "h": 2 * N_LINES - 2,
                                        },
                                    ],
                                    "xs": [
                                        {
                                            "i": "page-3-card-spectrum",
                                            "x": 0,
                                            "y": 2,
                                            "w": 4,
                                            "h": N_LINES,
                                        },
                                        {
                                            "i": "page-3-card-heatmap",
                                            "x": 0,
                                            "y": 14 + 7 + 5,
                                            "w": 4,
                                            "h": 2 * N_LINES - 2,
                                        },
                                        {
                                            "i": "page-3-card-graph-lipid-comparison",
                                            "x": 0,
                                            "y": 14 + 7 + 5 + N_LINES,
                                            "w": 4,
                                            "h": 2 * N_LINES - 3,
                                        },
                                    ],
                                    "xxs": [
                                        {
                                            "i": "page-3-card-spectrum",
                                            "x": 0,
                                            "y": 2,
                                            "w": 2,
                                            "h": N_LINES,
                                        },
                                        {
                                            "i": "page-3-card-heatmap",
                                            "x": 0,
                                            "y": 9 + 7 + 5,
                                            "w": 2,
                                            "h": 2 * N_LINES - 2,
                                        },
                                        {
                                            "i": "page-3-card-graph-lipid-comparison",
                                            "x": 0,
                                            "y": 9 + 7 + 5 + N_LINES,
                                            "w": 2,
                                            "h": 2 * N_LINES - 5,
                                        },
                                    ],
                                },
                                children=[
                                    dbc.Card(
                                        id="page-3-card-spectrum",
                                        style={
                                            "maxWidth": "100%",
                                            "margin": "0 auto",
                                            "width": "100%",
                                            "height": "100%",
                                        },
                                        children=[
                                            dbc.CardHeader(
                                                "High-resolution spectrum for current selection",
                                                style={
                                                    "background-color": "#1d1c1f",
                                                    "color": "white",
                                                },
                                            ),
                                            dbc.CardBody(
                                                className="loading-wrapper py-0 my-0",
                                                style={"background-color": "#1d1c1f",},
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
                                                                                className="text-center my-5",
                                                                                children=html.Strong(
                                                                                    children="Please draw at least one region on the heatmap and clicked on 'compute spectra'.. and clicked on 'compute spectra'.",
                                                                                    style={
                                                                                        "color": "#df5034"
                                                                                    },
                                                                                ),
                                                                            ),
                                                                            html.Div(
                                                                                id="page-3-alert-2",
                                                                                className="text-center my-2",
                                                                                style={
                                                                                    "display": "none"
                                                                                },
                                                                                children=[
                                                                                    html.Strong(
                                                                                        children="Too many regions selected, please reset the annotations.",
                                                                                        style={
                                                                                            "color": "#df5034"
                                                                                        },
                                                                                    ),
                                                                                ],
                                                                            ),
                                                                        ],
                                                                    ),
                                                                    html.Div(
                                                                        id="page-3-graph-spectrum-per-pixel-wait"
                                                                    ),
                                                                    dcc.Graph(
                                                                        id="page-3-graph-spectrum-per-pixel",
                                                                        style={
                                                                            "height": HEIGHT_PLOTS
                                                                        }
                                                                        | {"display": "none"},
                                                                        config=basic_config
                                                                        | {
                                                                            "toImageButtonOptions": {
                                                                                "format": "png",
                                                                                "filename": "spectrum_from_custom_region",
                                                                                "scale": 2,
                                                                            }
                                                                        },
                                                                    ),
                                                                    dmc.Button(
                                                                        children="Download spectrum data",
                                                                        id="page-3-download-data-button",
                                                                        disabled=False,
                                                                        variant="filled",
                                                                        radius="md",
                                                                        size="xs",
                                                                        color="cyan",
                                                                        compact=False,
                                                                        loading=False,
                                                                        # lass_name="mr-5",
                                                                        style={
                                                                            "position": "absolute",
                                                                            "top": "3rem",
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
                                    dbc.Card(
                                        id="page-3-card-heatmap",
                                        style={
                                            "maxWidth": "100%",
                                            "margin": "0 auto",
                                            "width": "100%",
                                            "height": "100%",
                                        },
                                        children=[
                                            dbc.CardHeader(
                                                "Average lipid expression per selection",
                                                style={
                                                    "background-color": "#1d1c1f",
                                                    "color": "white",
                                                },
                                            ),
                                            dbc.CardBody(
                                                className="loading-wrapper mb-0 pb-0",
                                                style={"background-color": "#1d1c1f",},
                                                children=[
                                                    html.Div(
                                                        id="page-3-alert-3",
                                                        className="text-center my-5",
                                                        children=html.Strong(
                                                            children="Please draw at least one region on the heatmap and clicked on 'compute spectra'.",
                                                            style={"color": "#df5034"},
                                                        ),
                                                    ),
                                                    html.Div(
                                                        children=[
                                                            dcc.Slider(
                                                                id="page-4-slider",
                                                                className="my-2",
                                                                min=0,
                                                                max=99,
                                                                value=10,
                                                                marks={
                                                                    0: {"label": "No filtering"},
                                                                    25: {"label": "25%"},
                                                                    50: {"label": "50%"},
                                                                    75: {"label": "75%"},
                                                                    99: {
                                                                        "label": "99%",
                                                                        "style": {"color": "#f50"},
                                                                    },
                                                                },
                                                            ),
                                                            # dmc.Slider(
                                                            #     id="page-4-slider",
                                                            #     class_name="mt-2",
                                                            #     color="cyan",
                                                            #     min=0,
                                                            #     max=99,
                                                            #     step=3,
                                                            #     value=10,
                                                            #     size="xs",
                                                            #     # label="Filter lipid by percentile",
                                                            # ),
                                                            dbc.Spinner(
                                                                color="sucess",
                                                                children=[
                                                                    html.Div(
                                                                        id="page-3-graph-heatmap-per-lipid-wait"
                                                                    ),
                                                                    dcc.Graph(
                                                                        id="page-3-graph-heatmap-per-lipid",
                                                                        className="mb-1",
                                                                        style={
                                                                            "height": 2
                                                                            * HEIGHT_PLOTS,
                                                                            "background-color": "#1d1c1f",
                                                                        },
                                                                        # | {"display": "none"},
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
                                    dbc.Card(
                                        id="page-3-card-graph-lipid-comparison",
                                        style={
                                            "maxWidth": "100%",
                                            "margin": "0 auto",
                                            "width": "100%",
                                            "height": "100%",
                                            "overflow": "hidden",
                                        },
                                        children=[
                                            dbc.CardHeader(
                                                className="d-flex justify-content-between",
                                                style={
                                                    "background-color": "#1d1c1f",
                                                    "color": "white",
                                                },
                                                children=[
                                                    html.Div(
                                                        "Lipid intensity comparison",
                                                        className="mr-5",
                                                    ),
                                                    dmc.Switch(
                                                        id="page-3-toggle-mask",
                                                        label="Toggle masks and shape display",
                                                        checked=False,
                                                        color="cyan",
                                                        radius="xl",
                                                        size="sm",
                                                        class_name="ml-5",
                                                    ),
                                                ],
                                            ),
                                            dbc.CardBody(
                                                id="page-3-graph-lipid-comparison",
                                                style={"background-color": "#1d1c1f",},
                                                # className="loading-wrapper pt-0 mt-0 pb-0 mb-1 px-0 mx-0",
                                                children=[
                                                    html.Div(
                                                        id="page-3-alert-5",
                                                        className="text-center my-5",
                                                        children=html.Strong(
                                                            children="Please draw at least one region on the heatmap and clicked on 'compute spectra'..",
                                                            style={"color": "#df5034"},
                                                        ),
                                                    ),
                                                    dbc.Spinner(
                                                        color="dark",
                                                        children=[
                                                            html.Div(
                                                                id="page-3-graph-lipid--comparison-wait"
                                                            ),
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
                                                                            "top": "4rem",
                                                                        },
                                                                    ),
                                                                    dmc.Group(
                                                                        spacing="xs",
                                                                        align="flex-start",
                                                                        children=[
                                                                            dcc.Dropdown(
                                                                                id="page-3-dropdown-red",
                                                                                options=[],
                                                                                value=[],
                                                                                searchable=True,
                                                                                multi=True,
                                                                                placeholder="Choose up to 3 lipids",
                                                                                clearable=False,
                                                                                style={
                                                                                    "width": "15em",
                                                                                },
                                                                            ),
                                                                            dcc.Dropdown(
                                                                                id="page-3-dropdown-green",
                                                                                options=[],
                                                                                value=[],
                                                                                searchable=True,
                                                                                multi=True,
                                                                                placeholder="Choose up to 3 lipids",
                                                                                clearable=False,
                                                                                style={
                                                                                    "width": "15em",
                                                                                },
                                                                            ),
                                                                            dcc.Dropdown(
                                                                                id="page-3-dropdown-blue",
                                                                                options=[],
                                                                                value=[],
                                                                                searchable=True,
                                                                                multi=True,
                                                                                placeholder="Choose up to 3 lipids",
                                                                                clearable=False,
                                                                                style={
                                                                                    "width": "15em",
                                                                                },
                                                                            ),
                                                                            # dmc.MultiSelect(
                                                                            #     id="page-3-dropdown-blue",
                                                                            #     data=[],
                                                                            #     value=[],
                                                                            #     searchable=True,
                                                                            #     nothingFound="No lipid found",
                                                                            #     radius="md",
                                                                            #     size="xs",
                                                                            #     placeholder="Choose up to 3 lipids",
                                                                            #     clearable=False,
                                                                            #     maxSelectedValues=3,
                                                                            #     transitionDuration=150,
                                                                            #     transition="pop-top-left",
                                                                            #     transitionTimingFunction="ease",
                                                                            #     style={
                                                                            #         "width": "20em",
                                                                            #     },
                                                                            # ),
                                                                            dmc.Center(
                                                                                dmc.Button(
                                                                                    children="Visualize and compare",
                                                                                    id="page-3-open-modal",
                                                                                    variant="filled",
                                                                                    color="gray",
                                                                                    radius="md",
                                                                                    size="xs",
                                                                                    disabled=True,
                                                                                    compact=False,
                                                                                    loading=False,
                                                                                ),
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
                            dmc.Center(
                                class_name="w-100",
                                children=[
                                    dcc.Download(id="page-3-download-data"),
                                    dmc.Button(
                                        children="Close panel",
                                        id="page-4-close-drawer-region-selection",
                                        variant="filled",
                                        disabled=False,
                                        color="red",
                                        radius="md",
                                        size="xs",
                                        compact=False,
                                        loading=False,
                                        style={"position": "fixed", "top": "0.5rem"},
                                        class_name="w-50",
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )

    return page


###### APP CALLBACKS ######

# Function to display the hovered region
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
                (atlas.array_coordinates_warped_data[x, y, z] * 1000 / atlas.resolution).round(0),
                dtype=np.int16,
            )
            try:
                label = atlas.labels[tuple(slice_coor_rescaled)]
            except:
                label = "undefined"
            return "Hovered region: " + label

    return dash.no_update


# Function to reset the layout of the heatmap
@app.app.callback(
    Output("page-3-graph-heatmap-per-sel", "relayoutData"),
    Input("page-3-reset-button", "n_clicks"),
    Input("url", "pathname"),
    prevent_initial_call=True,
)
def page_3_reset_layout(cliked_reset, url):
    return {}


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
    relayoutData,
    slice_index,
    cliked_reset,
    l_mask_name,
    url,
    l_color_mask,
    reset,
    l_shapes_and_masks,
):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]

    if value_input != "hoverData":
        print(
            id_input, value_input, slice_index, cliked_reset, l_mask_name, url, l_color_mask, reset
        )

    # If a new slice is loaded or the page just got loaded
    # do nothing because of automatic relayout of the heatmap which is automatically triggered when the page is loaded
    if (
        id_input == "main-slider"
        or len(id_input) == 0
        or id_input == "page-3-reset-button"
        or id_input == "url"
    ):
        fig = return_shelved_object(
            "figures/load_page",
            "figure_basic_image",
            force_update=False,
            compute_function=figures.compute_figure_basic_image,
            type_figure="projection_corrected",
            index_image=slice_index - 1,
            plot_atlas_contours=False,
            draw=True,
        )
        fig.update_layout(
            dragmode="drawclosedpath",
            newshape=dict(
                fillcolor=config.l_colors[0], opacity=0.7, line=dict(color="white", width=1)
            ),
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
        and (l_mask_name is None or len(l_mask_name) == 0)
    ):
        fig = return_shelved_object(
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
            newshape=dict(
                fillcolor=config.l_colors[0], opacity=0.7, line=dict(color="white", width=1)
            ),
            autosize=True,
        )
        return fig, [], True, []

    if id_input == "page-3-graph-heatmap-per-sel" or id_input == "page-3-dropdown-brain-regions":
        # Rebuild figure
        fig = return_shelved_object(
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
        # l_shapes_and_masks = []
        if l_mask_name is not None:

            if len(l_mask_name) > 0:
                # dic_masks = return_shelved_object(
                #     "atlas/atlas_objects",
                #     "dic_masks_and_spectra",
                #     force_update=False,
                #     compute_function=atlas.compute_dic_projected_masks_and_spectra,
                #     slice_index=slice_index - 1,
                # )

                for idx_mask, mask_name in enumerate(l_mask_name):
                    id_name = atlas.dic_name_acronym[mask_name]
                    if id_name in atlas.dic_existing_masks[slice_index - 1]:
                        projected_mask = atlas.get_projected_mask_and_spectrum(
                            slice_index - 1, mask_name, MAIA_correction=False
                        )[0]
                    else:
                        logging.warning("The mask " + str(mask_name) + " couldn't be found")

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

                    l_images = [
                        normalized_projected_mask * color
                        for c, color in zip(["r", "g", "b", "a"], color_rgb)
                    ]
                    # Reoder axis to match plotly go.image requirements
                    array_image = np.moveaxis(np.array(l_images, dtype=np.uint8), 0, 2)

                    # convert image to string to save space (new image as each mask must have a different color)
                    base64_string = convert_image_to_base64(
                        array_image, optimize=True, format="gif", type="RGBA"
                    )
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
                            col_next = config.l_colors[
                                (len(relayoutData["shapes"]) + len(l_color_mask)) % 4
                            ]

                            # compute color and save in l_shapes_and_masks
                            if id_input == "page-3-graph-heatmap-per-sel":
                                color_idx_for_registration = len(l_color_mask)
                                if relayoutData is not None:
                                    if "shapes" in relayoutData:
                                        color_idx_for_registration += len(relayoutData["shapes"])
                                l_shapes_and_masks.append(
                                    [
                                        "shape",
                                        None,
                                        relayoutData["shapes"][-1],
                                        color_idx_for_registration - 1,
                                    ]
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


# Function that update dropdown options
@app.app.callback(
    Output("page-3-dropdown-brain-regions", "data"), Input("main-slider", "value"),
)
def page_3_update_dropdown_option(slice_index):

    if slice_index is not None:
        return [
            {"label": atlas.dic_acronym_name[node], "value": atlas.dic_acronym_name[node]}
            for node in atlas.dic_existing_masks[slice_index - 1]
        ]
    else:
        return dash.no_update


# Function that limits dropdown selection to 4
@app.app.callback(
    Output("page-3-dropdown-brain-regions", "disabled"),
    Input("page-3-dropdown-brain-regions", "value"),
    Input("page-3-reset-button", "n_clicks"),
    prevent_intial_call=True,
)
def page_3_disable_dropdown(l_selection, clicked_reset):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if id_input == "page-3-reset-button":
        return False

    if l_selection is not None:
        if len(l_selection) > 0 and len(l_selection) < 4:
            return False
        elif len(l_selection) >= 4:
            return True
    return dash.no_update


# Function that empties dropdown selection
@app.app.callback(
    Output("page-3-dropdown-brain-regions", "value"),
    Input("page-3-reset-button", "n_clicks"),
    Input("main-slider", "value"),
    prevent_initial_call=True,
)
def page_3_empty_dropdown(clicked_reset, slice_index):
    return []


# Function that activate the button to compute spectra
@app.app.callback(
    Output("page-3-button-compute-spectra", "disabled"),
    Input("page-3-graph-heatmap-per-sel", "relayoutData"),
    Input("page-3-reset-button", "n_clicks"),
    Input("page-3-dropdown-brain-regions", "value"),
    prevent_intial_call=True,
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


# Function to make visible the m/z plot in page 3
@app.app.callback(
    Output("page-3-graph-spectrum-per-pixel", "style"),
    Output("page-3-alert-2", "style"),
    Output("page-3-graph-heatmap-per-lipid", "style"),
    Input("page-3-reset-button", "n_clicks"),
    Input("page-3-button-compute-spectra", "n_clicks"),
    State("page-3-dropdown-brain-regions", "value"),
    State("page-3-graph-heatmap-per-sel", "relayoutData"),
    prevent_initial_call=True,
)
def page_3_display_high_res_mz_plot(clicked_reset, clicked_compute, mask, relayoutData):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if id_input == "page-3-reset-button":
        return {"display": "none"}, {"display": "none"}, {"display": "none"}

    elif id_input == "page-3-button-compute-spectra":
        logging.info("Compute spectra button has been clicked")

        if mask is not None:
            if mask != []:
                logging.info("One or several masks have been selected, displaying graphs")
                return (
                    {"height": HEIGHT_PLOTS},
                    {"display": "none"},
                    {"height": 2 * HEIGHT_PLOTS, "background-color": "#1d1c1f",},
                )

        if relayoutData is not None:
            if "shapes" in relayoutData:
                if len(relayoutData["shapes"]) > 0:
                    if len(relayoutData["shapes"]) <= 4:
                        logging.info("One or several shapes have been selected, displaying graphs")
                        return (
                            {"height": HEIGHT_PLOTS},
                            {"display": "none"},
                            {"height": 2 * HEIGHT_PLOTS, "background-color": "#1d1c1f",},
                        )
                    else:
                        return {"display": "none"}, {}, {"display": "none"}

    return dash.no_update


# Function to make visible the sorting switch for the lipid heatmap
@app.app.callback(
    Output("page-3-switches", "className"),
    # Input({"type":"page-3-button-compute-spectra", "index":ALL}, "n_clicks"),
    Input("page-3-reset-button", "n_clicks"),
    Input("page-3-graph-heatmap-per-lipid", "figure"),
    State("page-3-graph-heatmap-per-sel", "relayoutData"),
    prevent_initial_call=True,
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


# Function to make visible the alert regarding the m/z plot in page 3
@app.app.callback(
    Output("page-3-alert", "style"),
    Output("page-3-alert-3", "style"),
    Output("page-3-alert-5", "style"),
    Input("page-3-button-compute-spectra", "n_clicks"),
    Input("page-3-reset-button", "n_clicks"),
    State("page-3-graph-heatmap-per-sel", "relayoutData"),
    State("page-3-dropdown-brain-regions", "value"),
    prevent_initial_call=True,
)
def page_3_display_alert(clicked_compute, clicked_reset, relayoutData, mask):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if id_input == "page-3-reset-button":
        return {}, {}, {}

    elif id_input == "page-3-button-compute-spectra":
        if mask is not None:
            if mask != []:
                return (
                    {"display": "none"},
                    {"display": "none"},
                    {"display": "none"},
                )

        if relayoutData is not None:
            if "shapes" in relayoutData:
                if len(relayoutData["shapes"]) > 0:
                    return (
                        {"display": "none"},
                        {"display": "none"},
                        {"display": "none"},
                    )
    return dash.no_update


# Global function to memoize/compute spectrum
@cache_flask.memoize()
def global_spectrum_store(
    slice_index, l_shapes_and_masks, l_mask_name, relayoutData, as_enrichment, log_transform
):
    l_spectra = []
    idx_mask = -1
    idx_path = -1

    logging.info("Computing spectra now")
    # print("ICI1", l_shapes_and_masks)
    # print("ICI2", l_mask_name)

    for shape in l_shapes_and_masks:
        grah_scattergl_data = None
        # Compute average spectrum from mask
        if shape[0] == "mask":
            idx_mask += 1
            mask_name = l_mask_name[idx_mask]
            id_name = atlas.dic_name_acronym[mask_name]
            if id_name in atlas.dic_existing_masks[slice_index - 1]:
                grah_scattergl_data = atlas.get_projected_mask_and_spectrum(
                    slice_index - 1, mask_name, MAIA_correction=False
                )[1]
            else:
                logging.warning("Bug, the selected mask does't exist")
                return dash.no_update

        elif shape[0] == "shape":
            idx_path += 1

            logging.info("Start computing path")
            l_paths = []
            for shape in relayoutData["shapes"]:
                if "path" in shape:
                    # get condensed path version of the annotation
                    parsed_path = shape["path"][1:-1].replace("L", ",").split(",")
                    path = [round(float(x)) for x in parsed_path]

                    # Work with image projection (check previous version if need to work with original image)
                    path = [
                        (
                            int(
                                atlas.array_projection_correspondence_corrected[
                                    slice_index - 1, y, x, 0
                                ]
                            ),  # must explicitely cast to int for serialization as numpy int are not accepted
                            int(
                                atlas.array_projection_correspondence_corrected[
                                    slice_index - 1, y, x, 1
                                ]
                            ),
                        )
                        for x, y in zip(path[:-1:2], path[1::2])
                    ]
                    # clean path from artefacts due to projection
                    path = [
                        t for t in list(dict.fromkeys(path)) if -1 not in t
                    ]  # use dic key to remove duplicates created by the correction of the projection

                    if len(path) > 0:
                        path.append(path[0])  # to close the path
                    l_paths.append(path)
            logging.info("Computing path finished")

            try:
                path = l_paths[idx_path]
                if len(path) > 0:
                    list_index_bound_rows, list_index_bound_column_per_row = sample_rows_from_path(
                        np.array(path, dtype=np.int32)
                    )

                    grah_scattergl_data = compute_spectrum_per_row_selection(
                        list_index_bound_rows,
                        list_index_bound_column_per_row,
                        data.get_array_spectra(slice_index),
                        data.get_array_lookup_pixels(slice_index),
                        data.get_image_shape(slice_index),
                        data.get_array_peaks_transformed_lipids(slice_index),
                        data.get_array_corrective_factors(slice_index),
                        zeros_extend=False,
                        apply_correction=False,
                    )
            except:
                logging.warning("Bug, the selected path does't exist")
                return None
        else:
            logging.warning("Bug, the shape type doesn't exit")
            return None

        # Do the selected transformations
        if grah_scattergl_data is not None:
            if as_enrichment:
                # first normalize with respect to itself
                grah_scattergl_data[1, :] /= np.sum(grah_scattergl_data[1, :])

                # then convert to uncompressed version
                grah_scattergl_data = convert_array_to_fine_grained(
                    grah_scattergl_data, 10 ** -3, lb=350, hb=1250
                )

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
        else:
            return None
    return l_spectra


# Function that takes path or mask and compute corresponding spectrum
@app.app.callback(
    Output("dcc-store-list-mz-spectra", "data"),
    Input("page-3-button-compute-spectra", "n_clicks"),
    Input("page-3-dcc-store-path-heatmap", "data"),
    Input("page-3-reset-button", "n_clicks"),
    Input("url", "pathname"),
    Input("main-slider", "value"),
    State("page-3-dropdown-brain-regions", "value"),
    State("dcc-store-shapes-and-masks", "data"),
    # Input("page-3-normalize", "checked"),
    # Input("page-3-log", "checked"),
    State("page-3-graph-heatmap-per-sel", "relayoutData"),
    State("session-id", "data"),
    prevent_intial_call=True,
)
def page_3_record_spectra(
    clicked_compute,
    l_paths,
    cliked_reset,
    url,
    slice_index,
    l_mask_name,
    l_shapes_and_masks,
    # as_enrichment,
    # log_transform,
    relayoutData,
    session_id,
):

    # Deactivated switches
    as_enrichment = False
    log_transform = False

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]

    # If a new slice is loaded or the page just got loaded, do nothing because
    # of automatic relayout of the heatmap which is automatically triggered when the page is loaded
    if len(id_input) == 0 or (value_input == "relayoutData" and relayoutData == {"autosize": True}):
        return dash.no_update

    # Delete everything when clicking reset
    elif id_input == "page-3-reset-button" or id_input == "url":
        return []

    elif id_input == "page-3-button-compute-spectra":
        logging.info("Starting to compute spectrum")

        l_spectra = global_spectrum_store(
            slice_index, l_shapes_and_masks, l_mask_name, relayoutData, as_enrichment, log_transform
        )

        # Set progress bar to 40 in redis db
        # r.set(session_id + "page-3-progress", 40)

        if l_spectra is not None:
            if l_spectra != []:
                logging.info("Spectra computed, returning it now")
                # return a dummy variable to indicate that the spectrum has been computed and trigger the callback
                return "ok"
        logging.warning("A bug appeared during spectrum computation")

    return []


# Function that takes path and plot spectrum
@app.app.callback(
    Output("page-3-graph-spectrum-per-pixel", "figure"),
    # Output("dcc-store-list-idx-lipids", "data"),
    # Output("page-3-empty-div-load", "children"),  # empty div to trigger spinner
    Input("page-3-reset-button", "n_clicks"),
    Input("dcc-store-list-mz-spectra", "data"),
    Input("main-slider", "value"),
    State("page-3-dropdown-brain-regions", "value"),
    State("dcc-store-shapes-and-masks", "data"),
    # Input("page-3-normalize", "checked"),
    # Input("page-3-log", "checked"),
    State("page-3-graph-heatmap-per-sel", "relayoutData"),
    prevent_intial_call=True,
)
def page_3_plot_spectrum(
    cliked_reset,
    l_spectra,
    slice_index,
    l_mask_name,
    l_shapes_and_masks,
    # as_enrichment,
    # log_transform,
    relayoutData,
):

    # Deactivated switches
    as_enrichment = False
    log_transform = False

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]

    # If a new slice is loaded or the page just got loaded, do nothing
    if len(id_input) == 0:
        return dash.no_update

    # Delete everything when clicking reset
    elif id_input == "page-3-reset-button" or l_spectra is None or l_spectra == []:
        return figures.return_empty_spectrum()

    # do nothing if l_spectra is None or []
    elif id_input == "dcc-store-list-mz-spectra":
        if len(l_spectra) > 0 or l_spectra == "ok":
            logging.info("Starting spectra plotting now")
            fig_mz = go.Figure()
            l_spectra = global_spectrum_store(
                slice_index,
                l_shapes_and_masks,
                l_mask_name,
                relayoutData,
                as_enrichment,
                log_transform,
            )
            ll_idx_labels = global_lipid_index_store(data, slice_index, l_spectra)
            for idx_spectra, (spectrum, l_idx_labels) in enumerate(zip(l_spectra, ll_idx_labels)):

                # Find color of the current spectrum
                col = config.l_colors[idx_spectra % 4]

                # Compute (again) the numpy array of the spectrum
                grah_scattergl_data = np.array(spectrum, dtype=np.float32)

                # almost no gain with numba :'(
                # two different functions so that's there's a unique output for each numba function
                @njit
                def return_idx_sup(l_idx_labels):
                    return [i for i, x in enumerate(l_idx_labels) if x >= 0]

                @njit
                def return_idx_inf(l_idx_labels):
                    return [i for i, x in enumerate(l_idx_labels) if x < 0]

                l_idx_kept = return_idx_sup(l_idx_labels)
                l_idx_unkept = return_idx_inf(l_idx_labels)

                # Pad annotated trace with zeros
                (
                    grah_scattergl_data_padded_annotated,
                    array_index_padding,
                ) = add_zeros_to_spectrum(
                    grah_scattergl_data[:, l_idx_kept], pad_individual_peaks=True, padding=10 ** -4,
                )
                l_mz_with_lipids = grah_scattergl_data_padded_annotated[0, :]
                l_intensity_with_lipids = grah_scattergl_data_padded_annotated[1, :]
                l_idx_labels_kept = l_idx_labels[l_idx_kept]

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
                l_labels_all_lipids = data.compute_l_labels()
                l_labels = [
                    l_labels_all_lipids[idx] if idx != -1 else "" for idx in l_idx_labels_kept
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
                    grah_scattergl_data[:, l_idx_unkept],
                    pad_individual_peaks=True,
                    padding=10 ** -4,
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
                template="plotly_dark",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.1),
            )
            fig_mz.layout.plot_bgcolor = "rgba(0,0,0,0)"
            fig_mz.layout.paper_bgcolor = "rgba(0,0,0,0)"

            logging.info("Spectra plotted. Returning it now")
            # Return dummy variable for ll_idx_labels to confirm that it has been computed
            return fig_mz

    return dash.no_update


# Function that plots heatmap representing lipid intensity from the current selection
@app.app.callback(
    Output("page-3-graph-heatmap-per-lipid", "figure"),
    Output("page-3-dcc-store-lipids-region", "data"),
    # Input("dcc-store-list-idx-lipids", "data"),
    Input("page-3-reset-button", "n_clicks"),
    Input("page-3-sort-by-diff-switch", "value"),
    Input("page-4-slider", "value"),
    Input("main-slider", "value"),
    Input("dcc-store-list-mz-spectra", "data"),
    State("page-3-dropdown-brain-regions", "value"),
    State("dcc-store-shapes-and-masks", "data"),
    # Input("page-3-normalize", "checked"),
    # Input("page-3-log", "checked"),
    State("page-3-graph-heatmap-per-sel", "relayoutData"),
    State("session-id", "data"),
    prevent_intial_call=True,
)
def page_3_draw_heatmap_per_lipid_selection(
    # ll_idx_labels,
    cliked_reset,
    sort_switch,
    percentile,
    slice_index,
    l_spectra,
    l_mask_name,
    l_shapes_and_masks,
    # as_enrichment,
    # log_transform,
    relayoutData,
    session_id,
):

    # Deactivated switches
    as_enrichment = False
    log_transform = False

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]

    # If a new slice is loaded or the page just got loaded, do nothing
    if len(id_input) == 0:
        return dash.no_update

    # Delete everything when clicking reset
    elif id_input == "page-3-reset-button":
        return figures.return_heatmap_lipid(), []

    # Otherwise compute lipid expression heatmap from spectrum
    elif (
        id_input == "dcc-store-list-idx-lipids"
        or id_input == "page-3-sort-by-diff-switch"
        or id_input == "page-3-scale-by-mean-switch"
        or id_input == "page-4-slider"
        or id_input == "dcc-store-list-mz-spectra"
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
        if l_spectra == "ok":  # and ll_idx_labels == "ok":
            # get the actual values for l_spectra and ll_idx_labels and not just the dummy fillings
            l_spectra = global_spectrum_store(
                slice_index,
                l_shapes_and_masks,
                l_mask_name,
                relayoutData,
                as_enrichment,
                log_transform,
            )
            ll_idx_labels = global_lipid_index_store(data, slice_index, l_spectra)
            if len(l_spectra) > 0:
                if len(ll_idx_labels) != len(l_spectra):
                    print(
                        "BUG: the number of received spectra is different from the number of received annotations"
                    )
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
                for i, (l_lipids, l_avg_intensity) in enumerate(
                    zip(ll_lipids_idx, ll_avg_intensity)
                ):
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
                        (
                            df_avg_intensity_lipids.std(axis=1)
                            / df_avg_intensity_lipids.mean(axis=1)
                        ).argsort(),
                        :,
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
                fig_heatmap_lipids.layout.template = "plotly_dark"
                fig_heatmap_lipids.layout.plot_bgcolor = "rgba(0,0,0,0)"
                fig_heatmap_lipids.layout.paper_bgcolor = "rgba(0,0,0,0)"
                logging.info("Heatmap computed. Returning it now")

                return fig_heatmap_lipids, l_idx_lipids

    return dash.no_update


# Function that sends the spectra of the selected region for download
@app.app.callback(
    Output("page-3-download-data", "data"),
    Input("page-3-download-data-button", "n_clicks"),
    State("page-3-graph-spectrum-per-pixel", "figure"),
    prevent_initial_call=True,
)
def page_3_download(n_clicks, fig_mz):
    if fig_mz is not None:
        fig_mz = go.Figure(data=fig_mz)
        if len(fig_mz.data) > 1:

            # Excel writer for download
            def to_excel(bytes_io):
                xlsx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
                for i, data in enumerate(fig_mz.data):
                    if i % 2 == 0:
                        df = pd.DataFrame.from_dict(
                            {"m/z": data["x"], "Intensity": data["y"], "Lipid": data["text"],}
                        )
                        df.to_excel(
                            xlsx_writer,
                            index=False,
                            sheet_name="Annotated spectrum sel " + str(i // 2 + 1),
                        )
                    else:
                        df = pd.DataFrame.from_dict({"m/z": data["x"], "Intensity": data["y"]})
                        df.to_excel(
                            xlsx_writer,
                            index=False,
                            sheet_name="Remaining spectrum sel " + str(i // 2 + 1),
                        )
                xlsx_writer.save()

            return dcc.send_data_frame(to_excel, "my_region_selection.xlsx")

    return dash.no_update


# Function that deactivate the download button if not region drawn
@app.app.callback(
    Output("page-3-download-data-button", "disabled"),
    Input("page-3-graph-spectrum-per-pixel", "figure"),
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
    prevent_initial_call=True,
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
                options = [
                    {"label": name, "value": str(idx)} for name, idx in zip(l_names, l_idx_lipids)
                ]

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
    prevent_initial_call=True,
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
    Input("page-3-open-modal", "n_clicks"),
    Input("page-3-reset-button", "n_clicks"),
    Input("page-3-toggle-mask", "checked"),
    Input("main-slider", "value"),
    State("page-3-dropdown-red", "value"),
    State("page-3-dropdown-green", "value"),
    State("page-3-dropdown-blue", "value"),
    State("dcc-store-shapes-and-masks", "data"),
    State("page-3-dropdown-brain-regions", "value"),
    State("dcc-store-color-mask", "data"),
    # Input("page-3-log", "checked"),
    # Input("page-3-normalize", "checked"),
    State("session-id", "data"),
    prevent_initial_call=True,
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
    # log_transform,
    # as_enrichment,
    session_id,
):

    # Deactivated switches
    as_enrichment = False
    log_transform = False

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    logging.info("Modal graph function triggered with input " + str(id_input))

    # Delete everything when clicking reset or changing slice index
    if id_input == "page-3-reset-button" or id_input == "main-slider":
        logging.info("Resetting modal graph")
        return figures.return_empty_spectrum()

    # Check that at least one lipid has been selected
    if len(l_red_lipids + l_green_lipids + l_blue_lipids) > 0:
        logging.info("At least one lipid has been selected, starting computing modal graph now.")
        df_names = data.get_annotations()[data.get_annotations()["slice"] == slice_index]
        # Build the list of mz boundaries for each peak
        l_lipid_bounds = [
            [
                (float(df_names.iloc[int(index)]["min"]), float(df_names.iloc[int(index)]["max"]),)
                if int(index) != -1
                else None
                for index in l_lipids
            ]
            for l_lipids in [l_red_lipids, l_green_lipids, l_blue_lipids]
        ]

        fig = figures.compute_rgb_image_per_lipid_selection(
            slice_index, l_lipid_bounds, enrichment=as_enrichment, log=log_transform
        )
        if boolean_mask:
            if l_shapes_and_masks is not None:
                l_draw = []
                for shape in l_shapes_and_masks:
                    if shape[0] == "mask":
                        base64_string = shape[2]
                        fig.add_trace(
                            go.Image(visible=True, source=base64_string, hoverinfo="skip")
                        )
                    elif shape[0] == "shape":
                        draw = shape[2]
                        l_draw.append(draw)

                fig["layout"]["shapes"] = tuple(l_draw)
                # else:
                #    fig["layout"]["shapes"] = tuple(list(fig["layout"]["shapes"]).append(draw))
        logging.info("Modal graph computed. Returning it now")

        # Set progress bar to 90 in redis db
        # r.set(session_id + "page-3-progress", 100)

        return fig

    logging.info("No lipid were selected, ignoring update.")
    return dash.no_update


@app.app.callback(
    Output("page-4-drawer-region-selection", "is_open"),
    Input("page-3-button-compute-spectra", "n_clicks"),
    Input("page-4-close-drawer-region-selection", "n_clicks"),
    [State("page-4-drawer-region-selection", "is_open")],
)
def toggle_offcanvas(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

