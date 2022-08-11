# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This file contains the home page of the app. """

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import dash
from dash import html, dcc
import dash_mantine_components as dmc
from dash.dependencies import Input, Output, State
from in_app_documentation.documentation import return_documentation
from app import app
import visdcc
from user_agents import parse

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
                dmc.Group(
                    direction="column",
                    align="stretch",
                    class_name="mt-4",
                    children=[
                        dmc.Alert(
                            "A connection of at least 10Mbps is recommended to comfortably use the"
                            " application.",
                            title="Information",
                            color="cyan",
                        ),
                        dmc.Alert(
                            "This app is not recommended for use on a mobile device.",
                            id="mobile-warning",
                            title="Information",
                            color="cyan",
                            class_name="d-none",
                        ),
                        dmc.Alert(
                            "Performance tends to be reduced on Safari, consider switching to"
                            " another browser if encountering issues.",
                            id="safari-warning",
                            title="Information",
                            color="cyan",
                            class_name="d-none",
                        ),
                    ],
                ),
            ),
            dmc.Center(
                class_name="w-100",
                children=[
                    dmc.Group(
                        class_name="mt-3",
                        direction="column",
                        align="center",
                        position="center",
                        children=[
                            dmc.Text(
                                "Welcome to the Lipid Brain Atlas Explorer",
                                style={
                                    "fontSize": 40,
                                    "color": "#dee2e6",
                                    "margin-bottom": "-15rem",
                                },
                                align="center",
                            ),
                            html.Div(id="rotating-brain"),
                            html.Div(
                                id="skeleton-rotating-brain",
                                children=dmc.Image(
                                    src="/assets/ressources/brain.png",
                                    height=500,
                                ),
                            ),
                            visdcc.Run_js(id="javascript"),
                            # Below logo text
                            dmc.Text(
                                "Please start exploring our data by using the navigation bar on the"
                                " left",
                                size="xl",
                                align="center",
                                color="dimmed",
                                # class_name="mt-4",
                                style={
                                    "margin-top": "-3rem",
                                },
                            ),
                            dmc.Center(
                                dmc.Button(
                                    "Read documentation",
                                    id="page-0-collapse-doc-button",
                                    class_name="mt-1",
                                    color="cyan",
                                ),
                            ),
                            # Documentation in a bottom drawer
                            dmc.Drawer(
                                children=return_documentation(app),
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
            dcc.Store(id="dcc-store-mobile"),
            dcc.Store(id="dcc-store-browser"),
        ],
    ),
)

# ==================================================================================================
# --- Callbacks
# ==================================================================================================


@app.callback(
    Output("documentation-offcanvas-home", "opened"),
    [Input("page-0-collapse-doc-button", "n_clicks")],
    [State("documentation-offcanvas-home", "opened")],
)
def toggle_collapse(n, is_open):
    """This callback will trigger the drawer displaying the app documentation."""
    if n:
        return not is_open
    return is_open


@app.long_callback(output=Output("javascript", "run"), inputs=[Input("main-slider", "data")])
def display_rotating_brain(x):
    """This callback loads some javascript code to display the rotating brain."""
    with open("js/rotating-brain.js") as f:
        js = f.read()
    return js


app.clientside_callback(
    """
    function(trigger) {
        browserInfo = navigator.userAgent;
        return browserInfo
    }
    """,
    Output("dcc-store-browser", "data"),
    Input("dcc-store-browser", "data"),
)


@app.callback(
    Output("safari-warning", "class_name"),
    Output("mobile-warning", "class_name"),
    Input("dcc-store-browser", "data"),
)
def update(JSoutput):
    user_agent = parse(JSoutput)
    safari_class = ""
    mobile_class = ""
    if not "Safari" in user_agent.browser.family:
        safari_class = "d-none"
    if user_agent.is_mobile is False:
        mobile_class = "d-none"

    return safari_class, mobile_class
