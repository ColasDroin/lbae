###### IMPORT MODULES ######

# Official modules
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash
import numpy as np
import dash_draggable
import logging
import dash_mantine_components as dmc

# Homemade modules
from lbae import app
from lbae.app import figures, data
from lbae.modules.tools.misc import return_pickled_object

###### DEFFINE PAGE LAYOUT ######
# ! It seems that some things (useless?) are loaded at startup and take time
#! Put basic config in config in all page file
def return_layout(basic_config, slice_index):

    page = dash_draggable.ResponsiveGridLayout(
        id="draggable",
        clearSavedLayout=True,
        isDraggable=False,
        isResizable=False,
        containerPadding=[2, 2],
        breakpoints={"xxl": 1600, "lg": 1200, "md": 996, "sm": 768, "xs": 480, "xxs": 0},
        gridCols={"xxl": 12, "lg": 12, "md": 10, "sm": 6, "xs": 4, "xxs": 2},
        layouts={
            # x sets the lateral position, y the vertical one, w is in columns (whose size depends on the dimension), h is in rows (30px)
            # nb columns go 12->10->6->4->2
            "xxl": [{"i": "page-1-main-toast", "x": 2, "y": 0, "w": 8, "h": 22},],
            "lg": [{"i": "page-1-main-toast", "x": 2, "y": 0, "w": 8, "h": 20},],
            "md": [{"i": "page-1-main-toast", "x": 1, "y": 0, "w": 8, "h": 18},],
            "sm": [{"i": "page-1-main-toast", "x": 0, "y": 0, "w": 6, "h": 17},],
            "xs": [{"i": "page-1-main-toast", "x": 0, "y": 0, "w": 4, "h": 14},],
            "xxs": [{"i": "page-1-main-toast", "x": 0, "y": 0, "w": 2, "h": 12},],
        },
        children=[
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
                                    dbc.Tab(label="Filtered slices", tab_id="page-1-tab-2"),
                                    dbc.Tab(label="Atlas slices", tab_id="page-1-tab-3"),
                                ],
                                id="page-1-card-tabs",
                                # card=True,
                                active_tab="page-1-tab-1",
                                # className="mr-5 pr-5",
                            ),
                            dbc.Switch(
                                id="page-1-toggle-annotations",
                                label="Annotations",
                                value=False,
                                className="ml-5 mt-2",
                            ),
                            dmc.Button(
                                "Display 3D slice distribution",
                                id="page-1-modal-button",
                                n_clicks=0,
                                class_name="ml-5",
                            ),
                        ],
                    ),
                    dbc.Modal(
                        [
                            dbc.ModalHeader(dbc.ModalTitle("3D slice distribution")),
                            dbc.ModalBody(
                                dbc.Spinner(
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
                                                    index_image=slice_index,
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
                                            # dbc.Col(
                                            #     width=1,
                                            #     className="px-0 mt-4 mr-1 text-right",
                                            #     children=[html.P("Slice: ")],
                                            # ),
                                            # ## Second column
                                            # dbc.Col(
                                            #     width=9,
                                            #     className="mt-3",
                                            #     children=[
                                            #         dcc.Slider(
                                            #             className="px-0 mx-0",
                                            #             id="page-1-slider-slice-selection",
                                            #             min=1,
                                            #             max=data.get_slice_number(),
                                            #             step=None,
                                            #             updatemode="drag",
                                            #             marks={
                                            #                 x: {
                                            #                     "label": str(x) if x % 2 == 0 else "",
                                            #                     "style": {"color": config.dic_colors["dark"]},
                                            #                 }
                                            #                 for x in range(1, data.get_slice_number() + 1,)
                                            #             },
                                            #             value=initial_slice,
                                            #         )
                                            #     ],
                                            # ),
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
    )
    return page


###### CALLBACKS ######
# Function to update the image from the slider
@app.app.callback(
    Output("page-1-graph-slice-selection", "figure"),
    Input("main-slider", "value"),
    Input("page-1-card-tabs", "active_tab"),
    Input("page-1-toggle-annotations", "value"),
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
    State("main-slider", "value"),
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
    Output("page-1-modal", "is_open"), Input("page-1-modal-button", "n_clicks"), State("page-1-modal", "is_open"),
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
            "figures/3D_page", "slices_3D", force_update=False, compute_function=figures.compute_figure_slices_3D
        )
    return dash.no_update

