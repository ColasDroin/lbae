###### IMPORT MODULES ######

# Official modules
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash
import dash_draggable

# App module
from lbae import app
from lbae.app import figures, atlas
from lbae.modules.tools.misc import return_pickled_object

###### DEFFINE PAGE LAYOUT ######


def return_layout(basic_config, slice_index=1):

    page = (
        dash_draggable.ResponsiveGridLayout(
            id="draggable",
            clearSavedLayout=True,
            isDraggable=False,
            isResizable=False,
            containerPadding=[2, 2],
            layouts={
                # x sets the lateral position, y the vertical one, w is in columns (whose size depends on the dimension), h is in rows (30px)
                # nb columns go 12->10->6->4->2
                "lg": [
                    {"i": "page-5-card-hierarchy", "x": 0, "y": 0, "w": 6, "h": 15},
                    {"i": "page-5-card-atlas-sections", "x": 6, "y": 0, "w": 6, "h": 15},
                    {"i": "page-5-card-atlas-3D", "x": 0, "y": 12, "w": 12, "h": 14},
                ],
                "md": [
                    {"i": "page-5-card-hierarchy", "x": 0, "y": 0, "w": 5, "h": 13},
                    {"i": "page-5-card-atlas-sections", "x": 6, "y": 0, "w": 5, "h": 13},
                    {"i": "page-5-card-atlas-3D", "x": 6, "y": 10, "w": 10, "h": 12},
                ],
                "sm": [
                    {"i": "page-5-card-hierarchy", "x": 0, "y": 12, "w": 6, "h": 19},
                    {"i": "page-5-card-atlas-sections", "x": 0, "y": 0, "w": 6, "h": 19},
                    {"i": "page-5-card-atlas-3D", "x": 0, "y": 12 + 12, "w": 6, "h": 14},
                ],
                "xs": [
                    {"i": "page-5-card-hierarchy", "x": 0, "y": 10, "w": 4, "h": 12},
                    {"i": "page-5-card-atlas-sections", "x": 0, "y": 0, "w": 4, "h": 12},
                    {"i": "page-5-card-atlas-3D", "x": 0, "y": 10 + 10, "w": 4, "h": 12},
                ],
                "xxs": [
                    {"i": "page-5-card-hierarchy", "x": 0, "y": 6, "w": 2, "h": 6},
                    {"i": "page-5-card-atlas-sections", "x": 0, "y": 0, "w": 2, "h": 11},
                    {"i": "page-5-card-atlas-3D", "x": 0, "y": 6 + 6, "w": 2, "h": 8},
                ],
            },
            children=[
                dbc.Card(
                    id="page-5-card-hierarchy",
                    style={"maxWidth": "100%", "margin": "0 auto", "width": "100%", "height": "100%"},
                    children=[
                        dbc.CardHeader(children="Atlas hierarchy"),
                        dbc.CardBody(
                            className="loading-wrapper",
                            children=[
                                dbc.Spinner(
                                    color="dark",
                                    children=[
                                        html.Div(
                                            className="page-1-fixed-aspect-ratio",
                                            children=[
                                                dcc.Graph(
                                                    id="page-5-graph-hierarchy",
                                                    config=basic_config
                                                    | {
                                                        "toImageButtonOptions": {
                                                            "format": "png",
                                                            "filename": "atlas_hierarchy",
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
                                                        "figures/atlas_page/3D",
                                                        "sunburst",
                                                        force_update=False,
                                                        compute_function=figures.compute_sunburst_figure,
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
                    id="page-5-card-atlas-sections",
                    style={"maxWidth": "100%", "margin": "0 auto", "width": "100%", "height": "100%"},
                    className="mt-2",
                    children=[
                        dbc.CardHeader(
                            className="d-flex",
                            children=[
                                dbc.Tabs(
                                    [
                                        dbc.Tab(label="Frontal view", tab_id="page-5-tab-1"),
                                        dbc.Tab(label="Horizontal view", tab_id="page-5-tab-2"),
                                        dbc.Tab(label="Sagittal view", tab_id="page-5-tab-3"),
                                    ],
                                    id="page-5-card-tabs",
                                    # card=True,
                                    active_tab="page-5-tab-1",
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
                                    className="page-1-fixed-aspect-ratio",
                                    children=[
                                        dcc.Graph(
                                            id="page-5-graph-3D-atlas-slices",
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
                                            figure=return_pickled_object(
                                                "figures/atlas_page/3D",
                                                "atlas_with_slider",
                                                force_update=False,
                                                compute_function=figures.compute_atlas_with_slider,
                                                view="frontal",
                                                contour=False,
                                            ),
                                        ),
                                        html.P(
                                            "Hovered region: ",
                                            id="page-5-tab-4",
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
                dbc.Card(
                    id="page-5-card-atlas-3D",
                    style={"maxWidth": "100%", "margin": "0 auto", "width": "100%", "height": "100%"},
                    children=[
                        dbc.CardHeader(children="3D brain representation"),
                        dbc.CardBody(
                            className="loading-wrapper",
                            children=[
                                dbc.Spinner(
                                    color="dark",
                                    children=[
                                        html.Div(
                                            className="page-5-fixed-aspect-ratio",
                                            children=[
                                                dcc.Graph(
                                                    id="page-5-graph-atlas-3d",
                                                    config=basic_config
                                                    | {
                                                        "toImageButtonOptions": {
                                                            "format": "png",
                                                            "filename": "atlas_3D",
                                                            "scale": 2,
                                                        },
                                                        "scrollZoom": False,
                                                    },
                                                    style={
                                                        "width": "100%",
                                                        "height": "100%",
                                                        "position": "absolute",
                                                        "left": "0",
                                                    },
                                                    figure=return_pickled_object(
                                                        "figures/atlas_page/3D",
                                                        "",
                                                        force_update=False,
                                                        compute_function=figures.compute_3D_figure,
                                                        structure=None,
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
            ],
        ),
    )

    return page


###### APP CALLBACKS ######
@app.app.callback(
    Output("page-5-graph-3D-atlas-slices", "figure"),
    [Input("page-5-card-tabs", "active_tab")],
    prevent_initial_call=True,
)
def tab_content(active_tab):
    view = None
    if active_tab[-1] == "1":
        view = "frontal"
    elif active_tab[-1] == "2":
        view = "horizontal"
    elif active_tab[-1] == "3":
        view = "sagittal"

    if view is not None:
        figure = return_pickled_object(
            "figures/3D_page",
            "atlas_with_slider",
            force_update=False,
            compute_function=figures.compute_atlas_with_slider,
            view=view,
            contour=False,
        )
        return figure
    else:
        return dash.no_update


@app.app.callback(
    Output("page-5-tab-4", "children"),
    Input("page-5-graph-3D-atlas-slices", "hoverData"),
    State("page-5-card-tabs", "active_tab"),
)
def page_4_hover(hoverData, active_tab):
    if hoverData is not None:
        if len(hoverData["points"]) > 0:
            if active_tab[-1] == "1":
                x = hoverData["points"][0]["curveNumber"] * atlas.subsampling_block
                z = hoverData["points"][0]["x"]
                y = hoverData["points"][0]["y"]
            elif active_tab[-1] == "2":
                y = hoverData["points"][0]["curveNumber"] * atlas.subsampling_block
                z = hoverData["points"][0]["x"]
                x = hoverData["points"][0]["y"]
            elif active_tab[-1] == "3":
                z = hoverData["points"][0]["curveNumber"] * atlas.subsampling_block
                y = hoverData["points"][0]["x"]
                x = hoverData["points"][0]["y"]

            return "Hovered region: " + atlas.labels[x, y, z]

    return dash.no_update


@app.app.callback(
    Output("page-5-graph-atlas-3d", "figure"), Input("page-5-graph-hierarchy", "clickData"),
)
def page_4_click(clickData):
    if clickData is not None:
        if "points" in clickData:
            label = clickData["points"][0]["label"]
            acronym = atlas.dic_name_id[label]
            print("New 3d figure loading: ", label, acronym)
            fig = return_pickled_object(
                "figures/atlas_page/3D",
                "",
                force_update=False,
                compute_function=figures.compute_3D_figure,
                structure=acronym,
            )
            return fig

    return dash.no_update

