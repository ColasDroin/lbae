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
                            {"i": "page-5-card-graph-scatter", "x": 2, "y": 0, "w": 5, "h": 20},
                            {"i": "page-5-card-graph-barplot", "x": 7, "y": 0, "w": 5, "h": 20},
                        ],
                        "lg": [
                            {"i": "page-5-card-graph-scatter", "x": 0, "y": 0, "w": 6, "h": 15},
                            {"i": "page-5-card-graph-barplot", "x": 6, "y": 0, "w": 6, "h": 15},
                        ],
                        "md": [
                            {"i": "page-5-card-graph-scatter", "x": 0, "y": 0, "w": 5, "h": 14},
                            {"i": "page-5-card-graph-barplot", "x": 5, "y": 0, "w": 5, "h": 14},
                        ],
                        "sm": [
                            {"i": "page-5-card-graph-scatter", "x": 0, "y": 0, "w": 6, "h": 14},
                            {"i": "page-5-card-graph-barplot", "x": 0, "y": 14, "w": 6, "h": 14},
                        ],
                        "xs": [
                            {"i": "page-5-card-graph-scatter", "x": 0, "y": 0, "w": 4, "h": 12},
                            {"i": "page-5-card-graph-barplot", "x": 0, "y": 12, "w": 4, "h": 12},
                        ],
                        "xxs": [
                            {"i": "page-5-card-graph-scatter", "x": 0, "y": 0, "w": 2, "h": 10},
                            {"i": "page-5-card-graph-barplot", "x": 0, "y": 10, "w": 2, "h": 10},
                        ],
                    },
                    children=[
                        dbc.Card(
                            id="page-5-card-graph-scatter",
                            style={
                                "width": "100%",
                                "height": "100%",
                                "background-color": "#1d1c1f",
                            },
                            children=[
                                dbc.CardBody(
                                    className="h-100",
                                    style={"background-color": "#1d1c1f"},
                                    children=[
                                        dcc.Graph(
                                            id="page-4-graph-region-selection",
                                            config=basic_config,
                                            style={},
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
                            id="page-5-card-graph-barplot",
                            children=[
                                dbc.CardBody(
                                    style={"background-color": "#1d1c1f"},
                                    # className="pt-1",
                                    children=[
                                        dcc.Graph(
                                            id="page-4-graph-region-selection",
                                            config=basic_config,
                                            style={},
                                            figure=figures.compute_barplot(brain_1=True),
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
