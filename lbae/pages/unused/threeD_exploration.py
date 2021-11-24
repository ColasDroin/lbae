###### IMPORT MODULES ######

# Official modules
import dash_bootstrap_components as dbc
from dash import dcc, html

# from dash.dependencies import Input, Output, State
from dash.dependencies import Input, Output, State
import dash
import plotly.graph_objects as go
import numpy as np
import pandas as pd

# App module
import app
from tools.SliceData import SliceData


###### DEFFINE PAGE LAYOUT ######


def return_layout(basic_config=app.basic_config, slice_index=1):

    page = html.Div(
        children=[
            ### First row
            dbc.Row(
                justify="center",
                children=[
                    ## First column
                    dbc.Col(
                        lg=5,
                        children=[
                            dbc.Card(
                                style={"maxWidth": "100%", "margin": "0 auto"},
                                children=[
                                    dbc.CardHeader(children="Atlas hierarchy"),
                                    dbc.CardBody(
                                        id="page-4-card-hierarchy",
                                        className="loading-wrapper",
                                        children=[
                                            dbc.Spinner(
                                                color="dark",
                                                children=[
                                                    dcc.Graph(
                                                        id="page-4-graph-hierarchy",
                                                        config=basic_config
                                                        | {
                                                            "toImageButtonOptions": {
                                                                "format": "png",
                                                                "filename": "atlas_hierarchy",
                                                                "scale": 2,
                                                            }
                                                        },
                                                        style={},
                                                        figure=app.slice_atlas.return_sunburst_figure(),
                                                    ),
                                                ],
                                            ),
                                            html.Div("‎‎‏‏‎ ‎"),
                                        ],
                                    ),
                                ],
                            ),
                            dbc.Card(
                                style={"maxWidth": "100%", "margin": "0 auto"},
                                className="mt-2",
                                children=[
                                    dbc.CardHeader(
                                        className="d-flex",
                                        children=[
                                            dbc.Tabs(
                                                [
                                                    dbc.Tab(label="Frontal view", tab_id="page-4-tab-1"),
                                                    dbc.Tab(label="Horizontal view", tab_id="page-4-tab-2"),
                                                    dbc.Tab(label="Sagittal view", tab_id="page-4-tab-3"),
                                                ],
                                                id="page-4-card-tabs",
                                                # card=True,
                                                active_tab="page-4-tab-1",
                                                className="mr-5 pr-5",
                                            ),
                                        ],
                                    ),
                                    dbc.CardBody(
                                        className="loading-wrapper",
                                        children=[
                                            # dbc.Spinner(
                                            #    color="dark",
                                            #    children=[
                                            html.Div(
                                                className="page-4-fixed-aspect-ratio",
                                                children=[
                                                    dcc.Graph(
                                                        id="page-4-graph-3D-atlas-slices",
                                                        config=basic_config
                                                        | {
                                                            "toImageButtonOptions": {
                                                                "format": "png",
                                                                "filename": "annotated_atlas_brain_slice",
                                                                "scale": 2,
                                                            }
                                                        },
                                                        style={
                                                            "width": "100%",
                                                            "height": "100%",
                                                            "position": "absolute",
                                                            "left": "0",
                                                        },
                                                        figure=app.slice_atlas.return_atlas_with_slider(
                                                            view="frontal", contour=False
                                                        ),
                                                    ),
                                                    html.P(
                                                        "Hovered region: ",
                                                        id="page-4-tab-4",
                                                        className="text-warning font-weight-bold position-absolute",
                                                        style={"left": "35%", "top": "2em"},
                                                    ),
                                                ],
                                            ),
                                            # ],
                                            # ),
                                            html.Div("‎‎‏‏‎ ‎"),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ## Second column
                    dbc.Col(
                        lg=7,
                        children=[
                            dbc.Card(
                                style={"maxWidth": "100%", "margin": "0 auto"},
                                children=[
                                    dbc.CardHeader(children="3D brain representation"),
                                    dbc.CardBody(
                                        className="loading-wrapper",
                                        children=[
                                            dbc.Spinner(
                                                color="dark",
                                                children=[
                                                    html.Div(
                                                        className="page-4-fixed-aspect-ratio",
                                                        children=[
                                                            dcc.Graph(
                                                                id="page-4-graph-atlas-3d",
                                                                config=basic_config
                                                                | {
                                                                    "toImageButtonOptions": {
                                                                        "format": "png",
                                                                        "filename": "atlas_3D",
                                                                        "scale": 2,
                                                                    }
                                                                },
                                                                style={
                                                                    "width": "100%",
                                                                    "height": "100%",
                                                                    "position": "absolute",
                                                                    "left": "0",
                                                                },
                                                                figure=app.slice_atlas.return_3D_figure(
                                                                    structure=None
                                                                ),
                                                            ),
                                                        ],
                                                    ),
                                                ],
                                            ),
                                            html.Div("‎‎‏‏‎ ‎"),
                                        ],
                                    ),
                                ],
                            ),
                            dbc.Card(
                                className="mt-2",
                                style={"maxWidth": "100%", "margin": "0 auto"},
                                children=[
                                    dbc.CardHeader(children="3D slice browsing"),
                                    dbc.CardBody(
                                        className="loading-wrapper",
                                        children=[
                                            dbc.Spinner(
                                                color="dark",
                                                children=[
                                                    html.Div(
                                                        className="page-4-fixed-aspect-ratio",
                                                        children=[
                                                            dcc.Graph(
                                                                id="page-4-graph-our-data-3d",
                                                                config=basic_config
                                                                | {
                                                                    "toImageButtonOptions": {
                                                                        "format": "png",
                                                                        "filename": "atlas_3D",
                                                                        "scale": 2,
                                                                    }
                                                                },
                                                                style={
                                                                    "width": "100%",
                                                                    "height": "100%",
                                                                    "position": "absolute",
                                                                    "left": "0",
                                                                },
                                                                figure=SliceData.return_figure_slices_3D(),
                                                            ),
                                                        ],
                                                    ),
                                                ],
                                            ),
                                            html.Div("‎‎‏‏‎ ‎"),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ]
    )

    return page


###### APP CALLBACKS ######
@app.app.callback(
    Output("page-4-graph-3D-atlas-slices", "figure"),
    [Input("page-4-card-tabs", "active_tab")],
    prevent_initial_call=True,
)
def tab_content(active_tab):
    if active_tab[-1] == "1":
        return app.slice_atlas.return_atlas_with_slider(view="frontal", contour=False)
    elif active_tab[-1] == "2":
        return app.slice_atlas.return_atlas_with_slider(view="horizontal", contour=False)
    elif active_tab[-1] == "3":
        return app.slice_atlas.return_atlas_with_slider(view="sagittal", contour=False)

    return dash.no_update


@app.app.callback(
    Output("page-4-tab-4", "children"),
    Input("page-4-graph-3D-atlas-slices", "hoverData"),
    State("page-4-card-tabs", "active_tab"),
)
def page_4_hover(hoverData, active_tab):
    if hoverData is not None:
        if len(hoverData["points"]) > 0:
            if active_tab[-1] == "1":
                x = hoverData["points"][0]["curveNumber"] * app.slice_atlas.subsampling_block
                z = hoverData["points"][0]["x"]
                y = hoverData["points"][0]["y"]
            elif active_tab[-1] == "2":
                y = hoverData["points"][0]["curveNumber"] * app.slice_atlas.subsampling_block
                z = hoverData["points"][0]["x"]
                x = hoverData["points"][0]["y"]
            elif active_tab[-1] == "3":
                z = hoverData["points"][0]["curveNumber"] * app.slice_atlas.subsampling_block
                y = hoverData["points"][0]["x"]
                x = hoverData["points"][0]["y"]

            return "Hovered region: " + app.slice_atlas.labels[x, y, z]

    return dash.no_update


# @app.app.callback(
#    Output("page-4-graph-hierarchy", "figure"), Input("page-4-graph-3D-atlas-slices", "figure"),
# )
# def page_4_hover(fig):
#    print(fig)
#    return dash.no_update


@app.app.callback(
    Output("page-4-graph-atlas-3d", "figure"), Input("page-4-graph-hierarchy", "clickData"),
)
def page_4_click(clickData):
    if clickData is not None:
        if "points" in clickData:
            label = clickData["points"][0]["label"]
            acronym = app.slice_atlas.dic_name_id[label]
            print("New 3d figure loading: ", label, acronym)
            return app.slice_atlas.return_3D_figure(structure=acronym)

    return dash.no_update

