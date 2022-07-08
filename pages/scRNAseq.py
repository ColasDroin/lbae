# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This file contains the page used to explore and compare lipid expression in three-dimensional
brain structures."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import dash_bootstrap_components as dbc
from dash import dcc, html, clientside_callback
import logging
import dash_draggable
from dash.dependencies import Input, Output, State
import numpy as np
import dash
import dash_mantine_components as dmc
import copy

# LBAE imports
from app import app, data, figures, storage, atlas, cache_flask

# ==================================================================================================
# --- Layout
# ==================================================================================================


def return_layout(basic_config, slice_index):

    page = (
        html.Div(
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
                # React grid for nice responsivity pattern
                dash_draggable.ResponsiveGridLayout(
                    id="draggable",
                    clearSavedLayout=True,
                    isDraggable=False,
                    isResizable=False,
                    containerPadding=[0, 0],
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
                    style={
                        "background-color": "#1d1c1f",
                    },
                    layouts={
                        # x sets the lateral position, y the vertical one, w is in columns (whose size
                        # depends on the dimension), h is in rows (30px)
                        # nb columns go 12->12->10->6->4->2
                        "xxl": [
                            {"i": "page-5-card-graph-scatter-3D", "x": 1, "y": 0, "w": 5, "h": 18},
                            {"i": "page-5-card-graph-barplot", "x": 6, "y": 0, "w": 5, "h": 18},
                            {
                                "i": "page-5-card-graph-heatmap-lipid",
                                "x": 1,
                                "y": 18,
                                "w": 5,
                                "h": 18,
                            },
                            {
                                "i": "page-5-card-graph-heatmap-genes",
                                "x": 6,
                                "y": 18,
                                "w": 5,
                                "h": 18,
                            },
                        ],
                        "lg": [
                            {"i": "page-5-card-graph-scatter", "x": 0, "y": 0, "w": 6, "h": 15},
                            {"i": "page-5-card-graph-barplot", "x": 6, "y": 0, "w": 6, "h": 15},
                            {
                                "i": "page-5-card-graph-heatmap-lipid",
                                "x": 0,
                                "y": 15,
                                "w": 6,
                                "h": 15,
                            },
                            {
                                "i": "page-5-card-graph-heatmap-genes",
                                "x": 6,
                                "y": 15,
                                "w": 6,
                                "h": 15,
                            },
                        ],
                        "md": [
                            {"i": "page-5-card-graph-scatter", "x": 0, "y": 0, "w": 5, "h": 14},
                            {"i": "page-5-card-graph-barplot", "x": 5, "y": 0, "w": 5, "h": 14},
                            {
                                "i": "page-5-card-graph-heatmap-lipid",
                                "x": 0,
                                "y": 14,
                                "w": 5,
                                "h": 14,
                            },
                            {
                                "i": "page-5-card-graph-heatmap-genes",
                                "x": 5,
                                "y": 14,
                                "w": 5,
                                "h": 14,
                            },
                        ],
                        "sm": [
                            {"i": "page-5-card-graph-scatter", "x": 0, "y": 0, "w": 6, "h": 14},
                            {"i": "page-5-card-graph-barplot", "x": 0, "y": 14, "w": 6, "h": 14},
                            {
                                "i": "page-5-card-graph-heatmap-lipid",
                                "x": 0,
                                "y": 28,
                                "w": 6,
                                "h": 14,
                            },
                            {
                                "i": "page-5-card-graph-heatmap-genes",
                                "x": 0,
                                "y": 42,
                                "w": 6,
                                "h": 14,
                            },
                        ],
                        "xs": [
                            {"i": "page-5-card-graph-scatter", "x": 0, "y": 0, "w": 4, "h": 12},
                            {"i": "page-5-card-graph-barplot", "x": 0, "y": 12, "w": 4, "h": 12},
                            {
                                "i": "page-5-card-graph-heatmap-lipid",
                                "x": 0,
                                "y": 24,
                                "w": 4,
                                "h": 12,
                            },
                            {
                                "i": "page-5-card-graph-heatmap-genes",
                                "x": 0,
                                "y": 36,
                                "w": 4,
                                "h": 12,
                            },
                        ],
                        "xxs": [
                            {"i": "page-5-card-graph-scatter", "x": 0, "y": 0, "w": 2, "h": 10},
                            {"i": "page-5-card-graph-barplot", "x": 0, "y": 10, "w": 2, "h": 10},
                            {
                                "i": "page-5-card-graph-heatmap-lipid",
                                "x": 0,
                                "y": 20,
                                "w": 2,
                                "h": 10,
                            },
                            {
                                "i": "page-5-card-graph-heatmap-genes",
                                "x": 0,
                                "y": 30,
                                "w": 2,
                                "h": 10,
                            },
                        ],
                    },
                    children=[
                        dbc.Card(
                            id="page-5-card-graph-scatter-3D",
                            style={
                                "width": "100%",
                                "height": "100%",
                                "background-color": "#1d1c1f",
                            },
                            className="p-0 m-0",
                            children=[
                                dbc.CardBody(
                                    style={"background-color": "#1d1c1f"},
                                    className="p-0 m-0",
                                    children=[
                                        dcc.Graph(
                                            id="page-5-graph-scatter-3D",
                                            config=basic_config,
                                            className="h-100 w-100",
                                            figure=storage.return_shelved_object(
                                                "figures/scRNAseq_page",
                                                "scatter3D",
                                                force_update=False,
                                                compute_function=figures.compute_scatter_3D,
                                            ),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        dbc.Card(
                            style={
                                "width": "100%",
                                "height": "100%",
                                "background-color": "#1d1c1f",
                            },
                            className="p-0 m-0",
                            id="page-5-card-graph-barplot",
                            children=[
                                dbc.CardBody(
                                    style={"background-color": "#1d1c1f"},
                                    className="p-0 m-0",
                                    children=[
                                        dcc.Graph(
                                            id="page-5-graph-barplot",
                                            config=basic_config,
                                            className="h-100 w-100",
                                            figure=figures.compute_barplot(
                                                brain_1=False, idx_dot=None
                                            ),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        dbc.Card(
                            style={
                                "width": "100%",
                                "height": "100%",
                                "background-color": "#1d1c1f",
                            },
                            className="p-0 m-0",
                            id="page-5-card-graph-heatmap-lipid",
                            children=[
                                dbc.CardBody(
                                    style={"background-color": "#1d1c1f"},
                                    className="p-0 m-0",
                                    children=[
                                        dbc.Spinner(
                                            color="dark",
                                            children=[
                                                html.Div(
                                                    className="fixed-aspect-ratio",
                                                    id="page-5-div-graph-heatmap-lipid",
                                                    children=[
                                                        dcc.Graph(
                                                            id="page-5-graph-heatmap-lipid",
                                                            config=basic_config
                                                            | {
                                                                "toImageButtonOptions": {
                                                                    "format": "png",
                                                                    "filename": "heatmap_lipid",
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
                                                        dcc.Dropdown(
                                                            id="page-5-dropdown-lipid",
                                                            options=figures._scRNAseq.l_name_lipids_brain_2,
                                                            value=[],
                                                            searchable=True,
                                                            multi=False,
                                                            placeholder="Choose a lipid",
                                                            clearable=False,
                                                            style={
                                                                "width": "15em",
                                                            },
                                                        ),
                                                    ],
                                                ),
                                            ],
                                        ),
                                        dmc.Button(
                                            children="Download plot",
                                            id="page-5-download-lipid-plot-button",
                                            disabled=False,
                                            variant="filled",
                                            radius="md",
                                            size="xs",
                                            color="cyan",
                                            compact=False,
                                            loading=False,
                                            style={
                                                "position": "absolute",
                                                "top": "0.7rem",
                                                "left": "15rem",
                                            },
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        dbc.Card(
                            style={
                                "width": "100%",
                                "height": "100%",
                                "background-color": "#1d1c1f",
                            },
                            className="p-0 m-0",
                            id="page-5-card-graph-heatmap-genes",
                            children=[
                                dbc.CardBody(
                                    style={"background-color": "#1d1c1f"},
                                    className="p-0 m-0",
                                    children=[
                                        dbc.Spinner(
                                            color="dark",
                                            children=[
                                                html.Div(
                                                    className="fixed-aspect-ratio",
                                                    id="page-5-div-graph-heatmap-genes",
                                                    children=[
                                                        dcc.Graph(
                                                            id="page-5-graph-heatmap-genes",
                                                            config=basic_config
                                                            | {
                                                                "toImageButtonOptions": {
                                                                    "format": "png",
                                                                    "filename": "heatmap_genes",
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
                                                                    id="page-5-dropdown-red",
                                                                    options=figures._scRNAseq.l_genes_brain_2,
                                                                    value=[],
                                                                    searchable=True,
                                                                    multi=False,
                                                                    placeholder="Choose a gene",
                                                                    clearable=False,
                                                                    style={
                                                                        "width": "15em",
                                                                    },
                                                                ),
                                                                dcc.Dropdown(
                                                                    id="page-5-dropdown-green",
                                                                    options=figures._scRNAseq.l_genes_brain_2,
                                                                    value=[],
                                                                    searchable=True,
                                                                    multi=False,
                                                                    placeholder="Choose a gene",
                                                                    clearable=False,
                                                                    style={
                                                                        "width": "15em",
                                                                    },
                                                                ),
                                                                dcc.Dropdown(
                                                                    id="page-5-dropdown-blue",
                                                                    options=figures._scRNAseq.l_genes_brain_2,
                                                                    value=[],
                                                                    searchable=True,
                                                                    multi=False,
                                                                    placeholder="Choose a gene",
                                                                    clearable=False,
                                                                    style={
                                                                        "width": "15em",
                                                                    },
                                                                ),
                                                                dmc.Center(
                                                                    dmc.Button(
                                                                        children=(
                                                                            "Visualize and compare"
                                                                        ),
                                                                        id="page-5-display-heatmap-genes",
                                                                        variant="filled",
                                                                        color="cyan",
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
                                        dmc.Button(
                                            children="Download plot",
                                            id="page-5-download-genes-plot-button",
                                            disabled=False,
                                            variant="filled",
                                            radius="md",
                                            size="xs",
                                            color="cyan",
                                            compact=False,
                                            loading=False,
                                            style={
                                                "position": "absolute",
                                                "top": "0.7rem",
                                                "left": "15rem",
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
    )

    return page


# ==================================================================================================
# --- Callbacks
# ==================================================================================================

# ! Update these callbacks to take into account brain 1 and 2 change

# Function to make visible the alert regarding the m/z plot in page 3
@app.callback(
    Output("page-5-graph-barplot", "figure"),
    Input("page-5-graph-scatter-3D", "clickData"),
    prevent_initial_call=True,
)
def page_5_update_barplot(clickData):
    """This callback updates the barplot with the data from the selected spot."""

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    # If a spot has has been clicked, update the barplot
    if id_input == "page-5-graph-scatter-3D":
        if clickData is not None:
            if "points" in clickData:
                if len(clickData["points"]) > 0:
                    idx_dot = clickData["points"][0]["pointNumber"]
                    return figures.compute_barplot(brain_1=False, idx_dot=idx_dot)

    return dash.no_update


# Function to make visible the alert regarding the m/z plot in page 3
@app.callback(
    Output("page-5-graph-heatmap-lipid", "figure"),
    Input("page-5-dropdown-lipid", "value"),
    Input("page-5-dropdown-red", "value"),
    Input("page-5-dropdown-green", "value"),
    Input("page-5-dropdown-blue", "value"),
    prevent_initial_call=True,
)
def page_5_update_heatmap_lipid(lipid, gene_1, gene_2, gene_3):
    """This callback updates the lipid and genes comparison heatmap with the selected lipid and selected genes."""

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    l_genes = [gene_1, gene_2, gene_3]

    # If a spot has has been clicked, update the barplot
    if id_input == "page-5-dropdown-lipid":
        if lipid is not None or gene_1 is not None or gene_2 is not None or gene_3 is not None:
            return figures.compute_heatmap_lipid_genes(lipid, l_genes, brain_1=False)

    return dash.no_update
