# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This file contains the home page of the app. """

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
from dash import html
import dash_mantine_components as dmc
from dash.dependencies import Input, Output, State
from documentation.documentation import return_documentation
import app
import visdcc

# ==================================================================================================
# --- Layout
# ==================================================================================================

layout = (
    html.Div(
        id="home-content",
        style={
            "position": "absolute",
            "top": "0px",
            "right": "0px",
            "bottom": "0px",
            "left": "6rem",
            "height": "100vh",
            "background-color": "#1d1c1f",
        },
        children=[
            dmc.Center(
                dmc.Alert(
                    "A connection of at least 10Mbps is recommended to comfortably use the"
                    " application.",
                    title="Information",
                    color="cyan",
                    class_name="mt-5",
                )
            ),
            dmc.Center(
                class_name="w-100",
                children=[
                    dmc.Group(
                        class_name="my-5 py-5",
                        direction="column",
                        align="center",
                        position="center",
                        children=[
                            dmc.Text(
                                "Welcome to the Lipid Brain Atlas Explorer",
                                style={"fontSize": 40, "color": "#dee2e6"},
                                align="center",
                            ),
                            html.Div(id="rotating-brain"),
                            visdcc.Run_js(id="javascript"),
                            # Below logo text
                            dmc.Text(
                                "Please start exploring our data by using the navigation bar on the"
                                " right",
                                size="xl",
                                align="center",
                                color="dimmed",
                                # class_name="mt-4",
                            ),
                            dmc.Center(
                                dmc.Button(
                                    "Read documentation",
                                    id="page-0-collapse-doc-button",
                                    class_name="mt-4",
                                    color="cyan",
                                ),
                            ),
                            # Documentation in a bottom drawer
                            dmc.Drawer(
                                children=return_documentation(app.app),
                                id="documentation-offcanvas-home",
                                opened=False,
                                padding="md",
                                size="90vh",
                                position="bottom",
                            ),
                        ],
                    ),
                ],
            ),
        ],
    ),
)

# ==================================================================================================
# --- Callbacks
# ==================================================================================================


@app.app.callback(
    Output("documentation-offcanvas-home", "opened"),
    [Input("page-0-collapse-doc-button", "n_clicks")],
    [State("documentation-offcanvas-home", "opened")],
)
def toggle_collapse(n, is_open):
    """This callback will trigger the drawer displaying the app documentation"""
    if n:
        return not is_open
    return is_open


@app.app.callback(Output("javascript", "run"), [Input("main-slider", "value")])
def display_rotating_brain(x):
    with open("js/rotating-brain.js") as f:
        js = f.read()
    return js
