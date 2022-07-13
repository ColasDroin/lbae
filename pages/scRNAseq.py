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


def return_layout(basic_config, slice_index, brain):

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
                                "x": 3,
                                "y": 18,
                                "w": 6,
                                "h": 15,
                            },
                        ],
                        "lg": [
                            {"i": "page-5-card-graph-scatter-3D", "x": 0, "y": 0, "w": 6, "h": 13},
                            {"i": "page-5-card-graph-barplot", "x": 6, "y": 0, "w": 6, "h": 13},
                            {
                                "i": "page-5-card-graph-heatmap-lipid",
                                "x": 1,
                                "y": 13,
                                "w": 10,
                                "h": 15,
                            },
                        ],
                        "md": [
                            {"i": "page-5-card-graph-scatter-3D", "x": 0, "y": 0, "w": 5, "h": 13},
                            {"i": "page-5-card-graph-barplot", "x": 5, "y": 0, "w": 5, "h": 13},
                            {
                                "i": "page-5-card-graph-heatmap-lipid",
                                "x": 1,
                                "y": 13,
                                "w": 8,
                                "h": 14,
                            },
                        ],
                        "sm": [
                            {"i": "page-5-card-graph-scatter-3D", "x": 0, "y": 0, "w": 6, "h": 11},
                            {"i": "page-5-card-graph-barplot", "x": 0, "y": 14, "w": 6, "h": 11},
                            {
                                "i": "page-5-card-graph-heatmap-lipid",
                                "x": 0,
                                "y": 28,
                                "w": 6,
                                "h": 14,
                            },
                        ],
                        "xs": [
                            {"i": "page-5-card-graph-scatter-3D", "x": 0, "y": 0, "w": 4, "h": 12},
                            {"i": "page-5-card-graph-barplot", "x": 0, "y": 12, "w": 4, "h": 12},
                            {
                                "i": "page-5-card-graph-heatmap-lipid",
                                "x": 0,
                                "y": 24,
                                "w": 4,
                                "h": 12,
                            },
                        ],
                        "xxs": [
                            {"i": "page-5-card-graph-scatter-3D", "x": 0, "y": 0, "w": 2, "h": 10},
                            {"i": "page-5-card-graph-barplot", "x": 0, "y": 10, "w": 2, "h": 10},
                            {
                                "i": "page-5-card-graph-heatmap-lipid",
                                "x": 0,
                                "y": 20,
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
                                            className="d-none",
                                            style={
                                                "background-color": "#1d1c1f",
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
                                "overflow": "clip",
                            },
                            className="p-0 m-0",
                            id="page-5-card-graph-heatmap-lipid",
                            children=[
                                dbc.CardBody(
                                    style={"background-color": "#1d1c1f"},
                                    className="p-0 m-0",
                                    children=[
                                        html.Div(
                                            className="fixed-aspect-ratio",
                                            id="page-5-div-graph-heatmap-lipid",
                                            children=[
                                                # dmc.Center(
                                                #     dmc.Alert(
                                                #         "Please select a lipid, and up to three"
                                                #         " genes, and click the display button to"
                                                #         " see the data comparison.",
                                                #         id="page-5-alert-heatmap-lipid",
                                                #         title="Input needed",
                                                #         color="cyan",
                                                #         class_name="d-none",
                                                #     ),
                                                #     style={
                                                #         "width": "60%",
                                                #         "height": "100%",
                                                #         "position": "absolute",
                                                #         "left": "20%",
                                                #         "top": "0",
                                                #     },
                                                # ),
                                                dcc.Graph(
                                                    id="page-5-graph-heatmap-lipid",
                                                    figure=storage.return_shelved_object(
                                                        "figures/scRNAseq_page",
                                                        "base_heatmap_lipid",
                                                        force_update=False,
                                                        compute_function=figures.compute_heatmap_lipid_genes,
                                                        brain_1=True,
                                                    )
                                                    if brain == "brain_1"
                                                    else storage.return_shelved_object(
                                                        "figures/scRNAseq_page",
                                                        "base_heatmap_lipid",
                                                        force_update=False,
                                                        compute_function=figures.compute_heatmap_lipid_genes,
                                                        brain_1=False,
                                                    ),
                                                    config=basic_config
                                                    | {
                                                        "toImageButtonOptions": {
                                                            "format": "png",
                                                            "filename": "heatmap_lipid",
                                                            "scale": 2,
                                                        }
                                                    },
                                                    style={
                                                        "width": "60%",
                                                        # "height": "100%",
                                                        "position": "absolute",
                                                        "left": "20%",
                                                        "top": "0",
                                                    },
                                                    className="d-none",
                                                ),
                                                dbc.Progress(
                                                    id="page-5-progress-bar-structure",
                                                    color="#338297",
                                                    style={
                                                        "width": "50%",
                                                        "position": "absolute",
                                                        "left": "25%",
                                                        "top": "20%",
                                                    },
                                                    className="d-none",
                                                ),
                                                dmc.Group(
                                                    spacing="lg",
                                                    direction="column",
                                                    align="stretch",
                                                    style={
                                                        "width": "20%",
                                                        "position": "absolute",
                                                        "left": "1rem",
                                                        "top": "0",
                                                    },
                                                    grow=True,
                                                    children=[
                                                        dmc.Space(h="md"),
                                                        dmc.Group(
                                                            spacing="xs",
                                                            direction="column",
                                                            align="stretch",
                                                            grow=True,
                                                            children=[
                                                                dmc.Text("Select a lipid:"),
                                                                dcc.Dropdown(
                                                                    id="page-5-dropdown-lipid",
                                                                    options=figures._scRNAseq.l_name_lipids_brain_1
                                                                    if brain == "brain_1"
                                                                    else figures._scRNAseq.l_name_lipids_brain_2,
                                                                    searchable=True,
                                                                    # value="PA 34:1 K",
                                                                    multi=False,
                                                                    placeholder="Choose a lipid",
                                                                    clearable=False,
                                                                    style={
                                                                        "width": "100%",
                                                                    },
                                                                ),
                                                            ],
                                                        ),
                                                        dmc.Group(
                                                            spacing="xs",
                                                            direction="column",
                                                            align="stretch",
                                                            grow=True,
                                                            children=[
                                                                dmc.Text(
                                                                    "Select up to three genes:"
                                                                ),
                                                                dcc.Dropdown(
                                                                    id="page-5-dropdown-red",
                                                                    options=figures._scRNAseq.l_genes_brain_1
                                                                    if brain == "brain_1"
                                                                    else figures._scRNAseq.l_genes_brain_2,
                                                                    searchable=True,
                                                                    multi=False,
                                                                    # value="Nov",
                                                                    placeholder="Choose a gene",
                                                                    clearable=np.True_,
                                                                    style={
                                                                        "width": "100%",
                                                                    },
                                                                ),
                                                                dcc.Dropdown(
                                                                    id="page-5-dropdown-green",
                                                                    options=figures._scRNAseq.l_genes_brain_1
                                                                    if brain == "brain_1"
                                                                    else figures._scRNAseq.l_genes_brain_2,
                                                                    searchable=True,
                                                                    multi=False,
                                                                    # value="Mef2c",
                                                                    placeholder="Choose a gene",
                                                                    clearable=True,
                                                                    style={
                                                                        "width": "100%",
                                                                    },
                                                                ),
                                                                dcc.Dropdown(
                                                                    id="page-5-dropdown-blue",
                                                                    options=figures._scRNAseq.l_genes_brain_1
                                                                    if brain == "brain_1"
                                                                    else figures._scRNAseq.l_genes_brain_2,
                                                                    searchable=True,
                                                                    # value="Nnat",
                                                                    multi=False,
                                                                    placeholder="Choose a gene",
                                                                    clearable=True,
                                                                    style={
                                                                        "width": "100%",
                                                                    },
                                                                ),
                                                            ],
                                                        ),
                                                        dmc.Button(
                                                            children="Visualize and compare",
                                                            id="page-5-display-heatmap-genes",
                                                            variant="filled",
                                                            color="cyan",
                                                            radius="md",
                                                            size="xs",
                                                            disabled=False,
                                                            compact=False,
                                                            loading=False,
                                                            fullWidth=True,
                                                            class_name="mt-3",
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
                                                            fullWidth=True,
                                                        ),
                                                    ],
                                                ),
                                                dmc.Group(
                                                    spacing="lg",
                                                    direction="column",
                                                    align="stretch",
                                                    style={
                                                        "width": "20%",
                                                        "position": "absolute",
                                                        "left": "80%",
                                                        "top": "0",
                                                    },
                                                    grow=True,
                                                    children=[
                                                        dmc.Space(h="md"),
                                                        dmc.Text("Current selection:", size="lg"),
                                                        dmc.Group(
                                                            spacing="xs",
                                                            direction="column",
                                                            children=[
                                                                dmc.Text("Lipid:"),
                                                                dmc.Badge(
                                                                    id="page-5-badge-lipid",
                                                                    children="name-lipid-1",
                                                                    color="cyan",
                                                                    variant="filled",
                                                                ),
                                                            ],
                                                        ),
                                                        dmc.Group(
                                                            spacing="xs",
                                                            direction="column",
                                                            align="stretch",
                                                            grow=True,
                                                            children=[
                                                                dmc.Text("Genes:"),
                                                                dmc.Badge(
                                                                    id="page-5-badge-gene-1",
                                                                    children="name-gene-1",
                                                                    color="red",
                                                                    variant="filled",
                                                                ),
                                                                dmc.Badge(
                                                                    id="page-5-badge-gene-2",
                                                                    children="name-gene-2",
                                                                    color="green",
                                                                    variant="filled",
                                                                ),
                                                                dmc.Badge(
                                                                    id="page-5-badge-gene-3",
                                                                    children="name-gene-3",
                                                                    color="blue",
                                                                    variant="filled",
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
            ],
        ),
    )

    return page


# ==================================================================================================
# --- Callbacks
# ==================================================================================================


@app.callback(
    Output("page-5-graph-barplot", "figure"),
    Output("page-5-graph-barplot", "className"),
    Output("page-5-dropdown-lipid", "value"),
    Output("page-5-dropdown-red", "value"),
    Output("page-5-dropdown-green", "value"),
    Output("page-5-dropdown-blue", "value"),
    Input("page-5-graph-scatter-3D", "clickData"),
    Input("main-brain", "value"),
    prevent_initial_call=False,
)
def page_5_update_barplot(clickData, brain):
    """This callback updates the barplot with the data from the selected spot."""

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    # If a spot has has been clicked, update the barplot
    if id_input == "page-5-graph-scatter-3D":
        if clickData is not None:
            if "points" in clickData:
                if len(clickData["points"]) > 0:
                    idx_dot = clickData["points"][0]["pointNumber"]
                    (fig, l_genes, l_lipids,) = (
                        figures.compute_barplot(brain_1=True, idx_dot=idx_dot)
                        if brain == "brain_1"
                        else figures.compute_barplot(brain_1=False, idx_dot=idx_dot)
                    )
                    return fig, "w-100 h-100", l_lipids[0], l_genes[0], l_genes[1], l_genes[2]

    elif brain is not None:
        (fig, l_genes, l_lipids,) = (
            figures.compute_barplot(brain_1=True, idx_dot=None)
            if brain == "brain_1"
            else figures.compute_barplot(brain_1=False, idx_dot=None)
        )
    return fig, "w-100 h-100", l_lipids[0], l_genes[0], l_genes[1], l_genes[2]


@app.long_callback(
    output=Output("page-5-graph-heatmap-lipid", "figure"),
    inputs=[
        State("page-5-dropdown-lipid", "value"),
        State("page-5-dropdown-red", "value"),
        State("page-5-dropdown-green", "value"),
        State("page-5-dropdown-blue", "value"),
        Input("page-5-display-heatmap-genes", "n_clicks"),
        Input("main-brain", "value"),
    ],
    running=[
        (
            Output("page-5-progress-bar-structure", "className"),
            "",
            "d-none",
        ),
        (Output("page-5-download-lipid-plot-button", "disabled"), True, False),
        (Output("page-5-display-heatmap-genes", "disabled"), True, False),
        (Output("page-5-graph-heatmap-lipid", "className"), "d-none", ""),
    ],
    progress=[
        Output("page-5-progress-bar-structure", "value"),
        Output("page-5-progress-bar-structure", "label"),
    ],
    prevent_initial_call=True,
    cache_args_to_ignore=[4],
)
def page_5_update_heatmap_lipid(set_progress, lipid, gene_1, gene_2, gene_3, clicked, brain):
    """This callback updates the lipid and genes comparison heatmap with the selected lipid and
    selected genes."""

    # If no click has been done, just return nothing
    if clicked is None:
        return dash.no_update

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    # If a spot has has been clicked, update the barplot
    if lipid is not None or gene_1 is not None or gene_2 is not None or gene_3 is not None:
        l_genes = [gene_1, gene_2, gene_3]
        return (
            figures.compute_heatmap_lipid_genes(
                lipid, l_genes, brain_1=True, set_progress=set_progress
            )
            if brain == "brain_1"
            else figures.compute_heatmap_lipid_genes(
                lipid, l_genes, brain_1=False, set_progress=set_progress
            )
        )
    else:
        return {}


@app.callback(
    Output("page-5-badge-lipid", "children"),
    Output("page-5-badge-gene-1", "children"),
    Output("page-5-badge-gene-2", "children"),
    Output("page-5-badge-gene-3", "children"),
    Input("page-5-dropdown-lipid", "value"),
    Input("page-5-dropdown-red", "value"),
    Input("page-5-dropdown-green", "value"),
    Input("page-5-dropdown-blue", "value"),
    Input("page-5-display-heatmap-genes", "n_clicks"),
    State("page-5-badge-lipid", "children"),
    State("page-5-badge-gene-1", "children"),
    State("page-5-badge-gene-2", "children"),
    State("page-5-badge-gene-3", "children"),
    Input("main-brain", "value"),
)
def page_5_update_badge_names(
    lipid,
    gene_1,
    gene_2,
    gene_3,
    clicked,
    current_lipid,
    current_gene_1,
    current_gene_2,
    current_gene_3,
    brain,
):
    """This callback updates the lipid and genes comparison heatmap with the selected lipid and
    selected genes."""

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if id_input == "page-5-display-heatmap-genes" or id_input == "main-brain":
        return lipid, gene_1, gene_2, gene_3

    if (
        current_lipid == "name-lipid-1"
        and current_gene_1 == "name-gene-1"
        and current_gene_2 == "name-gene-2"
        and current_gene_3 == "name-gene-3"
    ):
        return lipid, gene_1, gene_2, gene_3

    return dash.no_update


@app.callback(
    Output("page-5-dropdown-lipid", "options"),
    Output("page-5-dropdown-red", "options"),
    Output("page-5-dropdown-green", "options"),
    Output("page-5-dropdown-blue", "options"),
    Input("main-brain", "value"),
)
def page_5_update_dropdown_options(brain):
    """This callback updates the lipid and genes dropdown options depening on the selected brain."""

    options_genes = (
        figures._scRNAseq.l_genes_brain_1
        if brain == "brain_1"
        else figures._scRNAseq.l_genes_brain_2
    )
    options_lipids = (
        figures._scRNAseq.l_name_lipids_brain_1
        if brain == "brain_1"
        else figures._scRNAseq.l_name_lipids_brain_2
    )

    return options_lipids, options_genes, options_genes, options_genes
