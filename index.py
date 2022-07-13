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
from app import app, data, atlas
from pages import (
    sidebar,
    home,
    load_slice,
    lipid_selection,
    region_analysis,
    threeD_exploration,
    scRNAseq,
)
from documentation.documentation import return_documentation
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
    # List of empty lipid indexes for the dropdown of page 4, assuming brain 1 is initially selected
    empty_lipid_list = [-1 for i in data.get_slice_list(indices="brain_1")]

    # Record session id in case sessions need to be individualized
    session_id = str(uuid.uuid4())

    # Define static content
    main_content = html.Div(
        children=[
            # To handle url since multi-page app
            dcc.Location(id="url", refresh=False),
            # Record session id, useful to trigger callbacks at initialization
            dcc.Store(id="session-id", data=session_id),
            # Record the slider index
            dcc.Store(id="main-slider", data=1),
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
                    dmc.Center(
                        id="main-paper-slider",
                        style={
                            "position": "fixed",
                            "bottom": "1rem",
                            "height": "3rem",
                            "left": "7rem",
                            "right": "1rem",
                            "background-color": "rgba(0, 0, 0, 0.0)",
                        },
                        children=[
                            dmc.Text(
                                id="main-text-slider",
                                children="Rostro-caudal coordinate (mm): ",
                                class_name="pr-4",
                                size="sm",
                            ),
                            dmc.Slider(
                                id="main-slider-1",
                                min=data.get_slice_list(indices="brain_1")[0],
                                max=data.get_slice_list(indices="brain_1")[-1],
                                step=1,
                                marks=[
                                    {
                                        "value": slice_index,
                                        # Use x coordinate for label
                                        "label": "{:.2f}".format(
                                            atlas.l_original_coor[slice_index - 1][0, 0][0]
                                        ),
                                    }
                                    for slice_index in data.get_slice_list(indices="brain_1")[::3]
                                ],
                                size="xs",
                                value=data.get_slice_list(indices="brain_1")[0],
                                color="cyan",
                                class_name="mt-2 mr-5 ml-2 mb-1 w-50",
                            ),
                            dmc.Slider(
                                id="main-slider-2",
                                min=data.get_slice_list(indices="brain_2")[0],
                                max=data.get_slice_list(indices="brain_2")[-1],
                                step=1,
                                marks=[
                                    {
                                        "value": slice_index,
                                        # Use x coordinate for label
                                        "label": "{:.2f}".format(
                                            atlas.l_original_coor[slice_index - 1][0, 0][0]
                                        ),
                                    }
                                    for slice_index in data.get_slice_list(indices="brain_2")[::3]
                                ],
                                size="xs",
                                value=data.get_slice_list(indices="brain_2")[0],
                                color="cyan",
                                class_name="mt-2 mr-5 ml-2 mb-1 w-50 d-none",
                            ),
                            dmc.Chips(
                                id="main-brain",
                                data=[
                                    {"value": "brain_1", "label": "Brain 1"},
                                    {"value": "brain_2", "label": "Brain 2"},
                                ],
                                value="brain_1",
                                class_name="pl-2 pt-1",
                                color="cyan",
                            ),
                        ],
                    ),
                    # Documentation in a bottom drawer
                    dmc.Drawer(
                        children=return_documentation(app),
                        id="documentation-offcanvas",
                        # title="LBAE documentation",
                        opened=False,
                        padding="md",
                        size="85vh",
                        position="bottom",
                    ),
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


def return_validation_layout(main_content, initial_slice=1, brain="brain_1"):
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
            scRNAseq.return_layout(basic_config, initial_slice, brain),
        ]
    )


# ==================================================================================================
# --- App callbacks
# ==================================================================================================
@app.callback(
    Output("content", "children"),
    Output("empty-content", "children"),
    Input("url", "pathname"),
    State("main-slider", "data"),
    State("main-brain", "value"),
)
def render_page_content(pathname, slice_index, brain):
    """This callback is used as a URL router."""

    # Keep track of the page in the console
    if pathname is not None:
        logging.info("Page" + pathname + " has been selected" + logmem())

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

    elif pathname == "/gene-data":
        page = scRNAseq.return_layout(basic_config, slice_index, brain)

    else:
        # If the user tries to reach a different page, return a 404 message
        page = dmc.Center(
            dmc.Alert(
                title="404: Not found",
                children=f"The pathname {pathname} was not recognised...",
                color="red",
                class_name="mt-5",
            ),
            class_name="mt-5",
        )
    return page, ""


@app.callback(
    Output("documentation-offcanvas", "opened"),
    [
        Input("sidebar-documentation", "n_clicks"),
    ],
    [State("documentation-offcanvas", "opened")],
)
def toggle_collapse(n1, is_open):
    """This callback triggers the modal windows that toggles the documentation when clicking on the
    corresponding button."""
    if n1:
        return not is_open
    return is_open


@app.callback(
    Output("main-paper-slider", "class_name"), Input("url", "pathname"), prevent_initial_call=False
)
def hide_slider(pathname):
    """This callback is used to hide the slider div when the user is on a page that does not need it."""

    # Pages in which the slider is displayed
    l_path_with_slider = [
        "/load-slice",
        "/lipid-selection",
        "/region-analysis",
        "/3D-exploration",
        "/gene-data",
    ]

    # Set the content according to the current pathname
    if pathname in l_path_with_slider:
        return ""

    else:
        return "d-none"


@app.callback(
    Output("main-slider-1", "style"),
    Output("main-slider-2", "style"),
    Output("main-text-slider", "style"),
    Input("url", "pathname"),
    prevent_initial_call=False,
)
def hide_slider_but_leave_brain(pathname):
    """This callback is used to hide the slider but leave brain chips when needed."""

    # Pages in which the slider is displayed
    l_path_without_slider_but_with_brain = [
        "/3D-exploration",
        "/gene-data",
    ]

    # Set the content according to the current pathname
    if pathname in l_path_without_slider_but_with_brain:
        return {"visibility": "hidden"}, {"visibility": "hidden"}, {"visibility": "hidden"}

    else:
        return {}, {}, {}


@app.callback(
    Output("main-slider-1", "class_name"),
    Output("main-slider-2", "class_name"),
    Output("main-slider-1", "value"),
    Output("main-slider-2", "value"),
    Input("main-brain", "value"),
    State("main-slider-1", "value"),
    State("main-slider-2", "value"),
    prevent_initial_call=False,
)
def hide_useless_slider(brain, value_1, value_2):
    """This callback is used to update the slider indices with the selected brain."""
    if brain == "brain_1":
        value_1 = value_2 - data.get_slice_list(indices="brain_1")[-1]
        return "mt-2 mr-5 ml-2 mb-1 w-50", "mt-2 mr-5 ml-2 mb-1 w-50 d-none", value_1, value_2
    elif brain == "brain_2":
        value_2 = value_1 + data.get_slice_list(indices="brain_1")[-1]
        return "mt-2 mr-5 ml-2 mb-1 w-50 d-none", "mt-2 mr-5 ml-2 mb-1 w-50", value_1, value_2


app.clientside_callback(
    """
    function(value_1, value_2, brain){
        if(brain == 'brain_1'){
            return value_1;
        }
        else if(brain == 'brain_2'){
            return value_2;
            }
    }
    """,
    Output("main-slider", "data"),
    Input("main-slider-1", "value"),
    Input("main-slider-2", "value"),
    State("main-brain", "value"),
)
"""This clientside callback is used to update the slider indices with the selected brain."""
