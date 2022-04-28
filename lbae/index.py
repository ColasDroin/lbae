# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This module is where the app layout is created: the main container, the sidebar and the 
different pages. All the dcc.store, used to store client data across pages, are created here. It is 
also here that the URL routing is done.
"""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
import uuid
import logging
import dash_mantine_components as dmc

# LBAE modules
from app import app, data
from pages import (
    sidebar,
    home,
    load_slice,
    lipid_selection,
    region_analysis,
    threeD_exploration,
)
from pages.documentation import return_documentation
from config import basic_config
from modules.tools.misc import logmem

# ==================================================================================================
# --- App layout
# ==================================================================================================


def return_main_content():
    """This function compute the elements of the app that are shared across pages, including all the
    dcc.store.

    Returns:
        html.Div: A div containing the corresponding elements.
    """
    # List of empty lipid indexes for the dropdown of page 4
    empty_lipid_list = [-1 for i in range(data.get_slice_number())]

    # Record session id in case sessions need to be individualized
    session_id = str(uuid.uuid4())

    # Define static content
    main_content = html.Div(
        children=[
            # To handle url since multi-page app
            dcc.Location(id="url", refresh=False),
            # Record session id, useful to trigger callbacks at initialization
            dcc.Store(id="session-id", data=session_id),
            # Record slice index, to keep track of current slice
            dcc.Store(id="dcc-store-slice-index", data=1),
            # Record the state of the range sliders for low and high resolution spectra in page 2
            dcc.Store(id="boundaries-low-resolution-mz-plot"),
            dcc.Store(id="boundaries-high-resolution-mz-plot"),
            # Record the lipids selected in page 2
            dcc.Store(id="page-2-selected-lipid-1", data=-1),
            dcc.Store(id="page-2-selected-lipid-2", data=-1),
            dcc.Store(id="page-2-selected-lipid-3", data=-1),
            dcc.Store(id="page-2-last-selected-lipids", data=[]),
            # Record the lipids selected in page 4
            dcc.Store(id="page-4-selected-lipid-1", data=empty_lipid_list),
            dcc.Store(id="page-4-selected-lipid-2", data=empty_lipid_list),
            dcc.Store(id="page-4-selected-lipid-3", data=empty_lipid_list),
            dcc.Store(id="page-4-last-selected-regions", data=[]),
            dcc.Store(id="page-4-selected-region-1", data=""),
            dcc.Store(id="page-4-selected-region-2", data=""),
            dcc.Store(id="page-4-selected-region-3", data=""),
            dcc.Store(id="page-4-last-selected-lipids", data=[]),
            # Record the shapes drawn in page 3
            dcc.Store(id="dcc-store-color-mask", data=[]),
            dcc.Store(id="dcc-store-reset", data=False),
            dcc.Store(id="dcc-store-shapes-and-masks", data=[]),
            dcc.Store(id="dcc-store-list-idx-lipids", data=[]),
            # Record the annotated paths drawn in page 3
            dcc.Store(id="page-3-dcc-store-path-heatmap"),
            dcc.Store(id="page-3-dcc-store-basic-figure", data=True),
            # Record the computed spectra drawn in page 3
            dcc.Store(id="dcc-store-list-mz-spectra", data=[]),
            # Record the lipids expressed in the region in page 3
            dcc.Store(id="page-3-dcc-store-lipids-region", data=[]),
            # Actual app layout
            html.Div(
                children=[
                    sidebar.layout,
                    html.Div(id="content"),
                    html.Div(
                        id="main-paper-slider",
                        style={
                            "position": "fixed",
                            "bottom": "0",
                            "height": "3rem",
                            "left": "6rem",  # "25%",
                            "right": 0,  # "20%",
                            "background-color": "#1d1c1f",
                        },
                        children=dmc.Slider(
                            id="main-slider",
                            min=1,
                            max=data.get_slice_number(),
                            step=1,
                            marks=[
                                {
                                    "value": slice_index,
                                    "label": str(slice_index),
                                }
                                for slice_index in range(1, data.get_slice_number() + 1, 3)
                            ],
                            # tooltip={"placement": "right", "always_visible": True,},
                            size="xs",
                            value=1,
                            color="cyan",
                            class_name="mt-2 mx-5",
                        ),
                    ),
                    # Documentation in a bottom drawer
                    dmc.Drawer(
                        children=return_documentation(),
                        id="documentation-offcanvas",
                        # title="LBAE documentation",
                        opened=False,
                        padding="md",
                        size="90vh",
                        position="bottom",
                    ),
                    # # Documentation in a lateral drawer
                    # dmc.Drawer(
                    #     id="drawer",
                    #     padding="md",
                    #     position="right",
                    #     size=500,
                    #     title="Page documentation",
                    #     children=[
                    #         dmc.Accordion(
                    #             children=[
                    #                 dmc.AccordionItem(
                    #                     children="""On any graph (heatmap or m/z plot), you can
                    #                         draw a square with your mouse to zoom in, and double
                    #                         click to reset zoom level.""",
                    #                     label="Zoom",
                    #                 ),
                    #                 dmc.AccordionItem(
                    #                     children="""You can interact more with the figures (zoom,
                    #                         pan, reset axes, download) using the modebard above
                    #                         them.""",
                    #                     label="Modebar",
                    #                 ),
                    #                 dmc.AccordionItem(
                    #                     children="""Most of the items in the app are embedded with
                    #                     advice. Just position your mouse over an item to get a tip
                    #                     on how to use it.""",
                    #                     label="Tooltips",
                    #                 ),
                    #             ],
                    #             iconPosition="right",
                    #             multiple=True,
                    #             id="acc",
                    #         ),
                    #     ],
                    # ),
                    # Spinner when switching pages
                    dbc.Spinner(
                        id="main-spinner",
                        color="light",
                        children=html.Div(id="empty-content"),
                        fullscreen=True,
                        fullscreen_style={"left": "6rem", "background-color": "#1d1c1f"},
                        spinner_style={"width": "6rem", "height": "6rem"},
                        delay_hide=100,
                    ),
                ],
            ),
        ],
    )
    return main_content


def return_validation_layout(main_content, initial_slice=1):
    """This function compute the layout of the app, including the main container, the sidebar and
    the different pages.

    Args:
        main_content (html.Div): A div containing the elements of the app that are shared across
            pages.
        initial_slice (int): Index of the slice to be displayed at launch.

    Returns:
        html.Div: A div containing the layout of the app.
    """
    return html.Div(
        [
            main_content,
            home.layout,
            load_slice.return_layout(basic_config, initial_slice),
            lipid_selection.return_layout(basic_config, initial_slice),
            region_analysis.return_layout(basic_config, initial_slice),
            threeD_exploration.return_layout(basic_config, initial_slice),
        ]
    )


# ==================================================================================================
# --- App callbacks
# ==================================================================================================
# ! Write docstring of callbacks when things are stabler


@app.callback(
    Output("content", "children"),
    Output("empty-content", "children"),
    Input("url", "pathname"),
    State("main-slider", "value"),
)
def render_page_content(pathname, slice_index):
    if pathname is not None:
        logging.info("Page" + pathname + "has been selected" + logmem())

    # Set the content according to the current pathname
    if pathname == "/":
        page = home.layout

    elif pathname == "/load-slice":
        page = load_slice.return_layout(basic_config, slice_index)

    elif pathname == "/lipid-selection":
        page = lipid_selection.return_layout(basic_config, slice_index)

    elif pathname == "/region-analysis":
        page = region_analysis.return_layout(basic_config, slice_index)

    elif pathname == "/3D-exploration":
        page = threeD_exploration.return_layout(basic_config, slice_index)
    # elif pathname == "/atlas-exploration":
    #    page = atlas_exploration_DEPRECATED.return_layout(basic_config, slice_index)

    else:
        # If the user tries to reach a different page, return a 404 message
        # ! To Fix, Jumbotron doesn't exist anymore
        page = dbc.Jumbotron(
            children=[
                html.H1("404: Not found", className="text-danger"),
                html.Hr(),
                html.P(f"The pathname {pathname} was not recognised..."),
            ]
        )
    return page, ""


# @app.callback(
#     Output("drawer", "opened"), Input("button-doc", "n_clicks"), prevent_initial_call=True
# )
# def drawer(n_clicks):
#     return True

# Callback for documentation
@app.callback(
    Output("documentation-offcanvas", "opened"),
    [
        Input("sidebar-documentation", "n_clicks"),
    ],  # Input("page-0-collapse-doc-button", "n_clicks")],
    [State("documentation-offcanvas", "opened")],
)
def toggle_collapse(n1, is_open):
    if n1:
        return not is_open
    return is_open


@app.callback(
    Output("main-paper-slider", "className"), Input("url", "pathname"), prevent_initial_call=False
)
def hide_slider(pathname):
    l_path_with_slider = ["/load-slice", "/lipid-selection", "/region-analysis"]
    # Set the content according to the current pathname
    if pathname in l_path_with_slider:
        return ""

    else:
        return "d-none"
