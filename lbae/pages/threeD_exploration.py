###### IMPORT MODULES ######

# Standard modules
import dash_bootstrap_components as dbc
from dash import dcc, html
import logging
import dash_draggable
from dash.dependencies import Input, Output, State
import numpy as np
import dash
import dash_mantine_components as dmc

# Data module
from app import figures, atlas, cache_flask
import app
from modules.tools.storage import return_shelved_object

###### DEFFINE PAGE LAYOUT ######


def return_layout(basic_config, slice_index):

    page = html.Div(
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
            # html.Div(className="mt-3"),
            dash_draggable.ResponsiveGridLayout(
                id="draggable",
                clearSavedLayout=True,
                isDraggable=False,
                isResizable=False,
                containerPadding=[2, 2],
                breakpoints={"xxl": 1600, "lg": 1200, "md": 996, "sm": 768, "xs": 480, "xxs": 0,},
                gridCols={"xxl": 12, "lg": 12, "md": 10, "sm": 6, "xs": 4, "xxs": 2,},
                style={"background-color": "#1d1c1f",},
                layouts={
                    # x sets the lateral position, y the vertical one, w is in columns (whose size depends on the dimension), h is in rows (30px)
                    # nb columns go 12->12->10->6->4->2
                    "xxl": [
                        {"i": "page-4-card-region-selection", "x": 3, "y": 0, "w": 6, "h": 16},
                        {"i": "page-4-card-lipid-selection", "x": 3, "y": 16, "w": 6, "h": 10},
                    ],
                    "lg": [
                        {"i": "page-4-card-region-selection", "x": 0, "y": 0, "w": 12, "h": 15},
                        {"i": "page-4-card-lipid-selection", "x": 0, "y": 14, "w": 12, "h": 10},
                    ],
                    "md": [
                        {"i": "page-4-card-region-selection", "x": 0, "y": 0, "w": 7, "h": 14},
                        {"i": "page-4-card-lipid-selection", "x": 6, "y": 0, "w": 3, "h": 12},
                    ],
                    "sm": [
                        {"i": "page-4-card-region-selection", "x": 0, "y": 0, "w": 6, "h": 19},
                        {"i": "page-4-card-lipid-selection", "x": 0, "y": 19, "w": 6, "h": 11},
                    ],
                    "xs": [
                        {"i": "page-4-card-region-selection", "x": 0, "y": 0, "w": 4, "h": 14},
                        {"i": "page-4-card-lipid-selection", "x": 0, "y": 0, "w": 4, "h": 11},
                    ],
                    "xxs": [
                        {"i": "page-4-card-region-selection", "x": 0, "y": 0, "w": 2, "h": 9},
                        {"i": "page-4-card-lipid-selection", "x": 0, "y": 0, "w": 2, "h": 10},
                    ],
                },
                children=[
                    dbc.Card(
                        id="page-4-card-region-selection",
                        style={"width": "100%", "height": "100%", "background-color": "#1d1c1f"},
                        children=[
                            # dbc.CardHeader(
                            #     children="",  # "Structure selection",
                            #     style={"background-color": "#1d1c1f", "color": "white",},
                            # ),
                            dbc.CardBody(
                                className="h-100",
                                style={"background-color": "#1d1c1f"},
                                children=[
                                    html.Div(
                                        className="d-flex",
                                        children=[
                                            html.Div(
                                                style={"display": "inline-block", "width": "70%"},
                                                children=[
                                                    dmc.Center(
                                                        dmc.Text(
                                                            "Select brain structure(s)",
                                                            size="xl",
                                                            color="white",
                                                        )
                                                    ),
                                                    dcc.Graph(
                                                        id="page-4-graph-region-selection",
                                                        config=basic_config,
                                                        style={
                                                            # "height": "100%",
                                                            # "position": "absolute",
                                                            # "left": "0",
                                                        },
                                                        figure=return_shelved_object(
                                                            "figures/atlas_page/3D",
                                                            "treemaps",
                                                            force_update=False,
                                                            compute_function=figures.compute_treemaps_figure,
                                                        ),
                                                    ),
                                                ],
                                            ),
                                            dmc.Group(
                                                direction="column",
                                                style={"display": "inline-block", "width": "30%"},
                                                align="center",
                                                class_name="ml-5",
                                                children=[
                                                    dmc.Center(
                                                        dmc.Text(
                                                            "Select lipid(s)",
                                                            size="xl",
                                                            class_name="mb-5 pb-5 ",
                                                            color="white",
                                                        )
                                                    ),
                                                    # dbc.Tooltip(
                                                    #     children="Please select the lipids of your choice (up to three):",
                                                    #     target="page-4-card-lipid-selection",
                                                    #     placement="left",
                                                    # ),
                                                    dmc.Select(
                                                        label="Select lipid category:",
                                                        placeholder="Select lipid cat",
                                                        id="page-4-dropdown-lipid-names",
                                                        data=[],
                                                        searchable=True,
                                                        nothingFound="No lipid found",
                                                        radius="md",
                                                        clearable=True,
                                                        size="xs",
                                                        transitionDuration=150,
                                                        transition="pop-top-left",
                                                        transitionTimingFunction="ease",
                                                    ),
                                                    dmc.Select(
                                                        label="Select lipid structure:",
                                                        placeholder="Select lipid struc",
                                                        id="page-4-dropdown-lipid-structures",
                                                        data=[],
                                                        searchable=True,
                                                        clearable=True,
                                                        nothingFound="No lipid found",
                                                        radius="md",
                                                        size="xs",
                                                        transitionDuration=150,
                                                        transition="pop-top-left",
                                                        transitionTimingFunction="ease",
                                                    ),
                                                    dmc.Select(
                                                        label="Select lipid cation:",
                                                        placeholder="Select lipid cat",
                                                        id="page-4-dropdown-lipid-cations",
                                                        data=[],
                                                        clearable=True,
                                                        searchable=True,
                                                        nothingFound="No lipid found",
                                                        radius="md",
                                                        size="xs",
                                                        transitionDuration=150,
                                                        transition="pop-top-left",
                                                        transitionTimingFunction="ease",
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        # className="d-flex justify-content-around",
                                        children=[
                                            html.Div(
                                                style={
                                                    "width": "calc(70% - 1.75rem)",
                                                    "display": "inline-block",
                                                },
                                                children=[
                                                    dmc.Button(
                                                        children="Please choose a structure above",
                                                        id="page-4-add-structure-button",
                                                        disabled=True,
                                                        variant="filled",
                                                        radius="md",
                                                        size="xs",
                                                        color="cyan",
                                                        compact=False,
                                                        loading=False,
                                                        fullWidth=True,
                                                        class_name="mr-5",
                                                    ),
                                                    dmc.Button(
                                                        children="Display lipid expression in the selected structure(s)",
                                                        id="page-4-display-button",
                                                        disabled=True,
                                                        variant="filled",
                                                        radius="md",
                                                        size="xs",
                                                        color="cyan",
                                                        compact=False,
                                                        loading=False,
                                                        fullWidth=True,
                                                        class_name="mr-5 mt-1",
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                style={
                                                    "width": "calc(30% - 1.25rem)",
                                                    "display": "inline-block",
                                                },
                                                children=[
                                                    dmc.Button(
                                                        children="Please choose a lipid above",
                                                        id="page-4-add-lipid-button",
                                                        disabled=True,
                                                        variant="filled",
                                                        radius="md",
                                                        color="cyan",
                                                        size="xs",
                                                        compact=False,
                                                        loading=False,
                                                        fullWidth=True,
                                                        class_name="ml-5",
                                                    ),
                                                    dmc.Button(
                                                        children="Compare lipid expression in the selected structures",
                                                        id="page-4-compare-structure-button",
                                                        disabled=True,
                                                        variant="filled",
                                                        radius="md",
                                                        size="xs",
                                                        color="cyan",
                                                        compact=False,
                                                        loading=False,
                                                        fullWidth=True,
                                                        class_name="ml-5 mt-1",
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                    dbc.Card(
                        style={
                            "maxWidth": "100%",
                            "margin": "0 auto",
                            "width": "100%",
                            "height": "100%",
                        },
                        id="page-4-card-lipid-selection",
                        children=[
                            # dbc.CardHeader(
                            #     children="",  # "Current selection",
                            #     style={"background-color": "#1d1c1f", "color": "white",},
                            # ),
                            dbc.CardBody(
                                style={"background-color": "#1d1c1f"},
                                className="pt-1",
                                children=[
                                    dmc.Group(
                                        direction="row",
                                        grow=True,
                                        align="flex-start",
                                        children=[
                                            dmc.Group(
                                                direction="column",
                                                grow=True,
                                                class_name="ml-5",
                                                children=[
                                                    dmc.Center(
                                                        class_name="w-100",
                                                        children=dmc.Text(
                                                            "Brain structure selection",
                                                            size="xl",
                                                            color="white",
                                                        ),
                                                    ),
                                                    dbc.Toast(
                                                        id="page-4-toast-region-1",
                                                        header="name-region-1",
                                                        # icon="primary",
                                                        dismissable=True,
                                                        is_open=False,
                                                        bodyClassName="p-0",
                                                        header_class_name="d-flex justify-content-center ml-2",
                                                        # className="mt-1",
                                                        style={"margin": "auto"},
                                                    ),
                                                    dbc.Toast(
                                                        id="page-4-toast-region-2",
                                                        header="name-region-2",
                                                        # icon="primary",
                                                        dismissable=True,
                                                        is_open=False,
                                                        bodyClassName="p-0",
                                                        header_class_name="d-flex justify-content-center ml-2",
                                                        # className="mt-1",
                                                        style={"margin": "auto"},
                                                    ),
                                                    dbc.Toast(
                                                        id="page-4-toast-region-3",
                                                        header="name-region-3",
                                                        # icon="primary",
                                                        dismissable=True,
                                                        is_open=False,
                                                        header_class_name="d-flex justify-content-center ml-2",
                                                        bodyClassName="p-0",
                                                        # className="mt-1",
                                                        style={"margin": "auto"},
                                                    ),
                                                ],
                                            ),
                                            dmc.Group(
                                                direction="column",
                                                # align="flex-start",
                                                # class_name="w-50",
                                                grow=True,
                                                class_name="ml-5",
                                                children=[
                                                    dmc.Center(
                                                        class_name="w-100",
                                                        children=dmc.Text(
                                                            "Lipid selection",
                                                            size="xl",
                                                            color="white",
                                                        ),
                                                    ),
                                                    dbc.Toast(
                                                        id="page-4-toast-lipid-1",
                                                        # header="name-lipid-1",
                                                        header="",
                                                        # icon="primary",
                                                        dismissable=True,
                                                        is_open=False,
                                                        bodyClassName="p-0",
                                                        header_class_name="d-flex justify-content-center ml-2",
                                                        # className="mt-1",
                                                        style={"margin": "auto"},
                                                    ),
                                                    dbc.Toast(
                                                        id="page-4-toast-lipid-2",
                                                        # header="name-lipid-2",
                                                        header="",
                                                        # icon="primary",
                                                        dismissable=True,
                                                        is_open=False,
                                                        bodyClassName="p-0",
                                                        header_class_name="d-flex justify-content-center ml-2",
                                                        # className="mt-1",
                                                        style={"margin": "auto"},
                                                    ),
                                                    dbc.Toast(
                                                        id="page-4-toast-lipid-3",
                                                        # header="name-lipid-3",
                                                        header="",
                                                        # icon="primary",
                                                        dismissable=True,
                                                        header_class_name="d-flex justify-content-center ml-2",
                                                        is_open=False,
                                                        bodyClassName="p-0",
                                                        # className="mt-1",
                                                        style={"margin": "auto",},
                                                    ),
                                                    # html.Div(
                                                    #     id="page-4-warning-lipids-number",
                                                    #     className="text-center mt-1",
                                                    #     children=html.Strong(
                                                    #         children="Please delete some lipids to choose new ones.",
                                                    #         style={"color": "#df5034"},
                                                    #     ),
                                                    # ),
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            dbc.Modal(
                                id="page-4-modal-volume",
                                is_open=False,
                                size="xl",
                                children=[
                                    dbc.ModalHeader(
                                        style={"background-color": "#1d1c1f",},
                                        children=dbc.ModalTitle(
                                            "Lipid selection interpolated in 3D",
                                            style={"color": "white"},
                                        ),
                                    ),
                                    dbc.ModalBody(
                                        style={"background-color": "#1d1c1f",},
                                        children=[
                                            dbc.Spinner(
                                                color="light",
                                                show_initially=False,
                                                children=[
                                                    html.Div(
                                                        className="page-1-fixed-aspect-ratio",
                                                        children=[
                                                            html.Div(
                                                                id="page-4-alert",
                                                                className="text-center my-2",
                                                                children=html.Strong(
                                                                    children="Please select at least one lipid.",
                                                                    style={"color": "#df5034"},
                                                                ),
                                                            ),
                                                            dcc.Graph(
                                                                id="page-4-graph-volume",
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
                                        ],
                                    ),
                                ],
                            ),
                            dbc.Modal(
                                id="page-4-modal-heatmap",
                                is_open=False,
                                scrollable=False,
                                size="xl",
                                style={
                                    "maxWidth": "100%",
                                    "margin": "0 auto",
                                    "width": "100%",
                                    "height": "100%",
                                },
                                children=[
                                    dbc.ModalHeader(
                                        style={"background-color": "#1d1c1f",},
                                        children=dbc.ModalTitle(
                                            "Lipid expression comparison", style={"color": "white"},
                                        ),
                                    ),
                                    dbc.ModalBody(
                                        className="d-flex justify-content-center flex-column",
                                        style={"background-color": "#1d1c1f",},
                                        children=[
                                            # dbc.CardHeader(className="d-flex", children="Lipid expression comparison",),
                                            # dbc.CardBody(
                                            #    className="py-0 mb-0 mt-2",
                                            #    children=[
                                            # dmc.RingProgress(
                                            #     id="page-4-progress-bar-structure",
                                            #     size=200,
                                            #     thickness=12,
                                            #     label="Loading data...",
                                            #     sections=[{"value": 0, "color": "red"},],
                                            # ),
                                            dbc.Progress(
                                                id="page-4-progress-bar-structure",
                                                style={"width ": "100%"},
                                                color="#ced4da",
                                            ),
                                            dcc.Slider(
                                                id="page-4-slider-percentile",
                                                min=0,
                                                max=99,
                                                value=80,
                                                marks={
                                                    0: {"label": "No filtering"},
                                                    25: {"label": "25%"},
                                                    50: {"label": "50%"},
                                                    75: {"label": "75%"},
                                                    99: {
                                                        "label": "99%",
                                                        "style": {"color": "#f50"},
                                                    },
                                                },
                                            ),
                                            # dbc.Spinner(
                                            #     color="dark",
                                            #     show_initially=False,
                                            #     children=[
                                            html.Div(
                                                # className="page-1-fixed-aspect-ratio",
                                                className="d-flex justify-content-center",
                                                style={"margin-top": "-5rem"},
                                                children=[
                                                    dcc.Graph(
                                                        id="page-4-graph-heatmap",
                                                        config=basic_config
                                                        | {
                                                            "toImageButtonOptions": {
                                                                "format": "png",
                                                                "filename": "brain_lipid_selection",
                                                                "scale": 2,
                                                            }
                                                        },
                                                        style={
                                                            # "width": "100%",
                                                            "height": "100%",
                                                            # "margin": "auto",
                                                            #    "position": "absolute",
                                                            #    "left": "0",
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
                ],
            ),
        ],
    )
    return page


###### APP CALLBACKS ######

# Function to make visible the alert regarding the plot page 4
@app.app.callback(
    Output("page-4-alert", "style"),
    Output("page-4-graph-volume", "style"),
    Input("page-4-display-button", "n_clicks"),
    State("page-4-last-selected-lipids", "data"),
)
def page_4_display_alert(clicked_compute, l_lipids):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if len(l_lipids) > 0:
        return (
            {"display": "none"},
            {"width": "100%", "height": "100%", "position": "absolute", "left": "0",},
        )

    else:
        return {}, {"display": "none"}


# Function to update label of the add structure button
@app.app.callback(
    Output("page-4-add-structure-button", "children"),
    Output("page-4-add-structure-button", "disabled"),
    Input("page-4-graph-region-selection", "clickData"),
    Input("page-4-selected-region-1", "data"),
    Input("page-4-selected-region-2", "data"),
    Input("page-4-selected-region-3", "data"),
)
def page_4_click(clickData, region_1_id, region_2_id, region_3_id):
    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if id_input == "page-4-graph-region-selection":
        if clickData is not None:
            if "points" in clickData:
                label = clickData["points"][0]["label"]
                # acronym = atlas.dic_name_acronym[label]
                return "Add " + label + " to selection", False
        return "Please choose a structure above", True

    # If lipids has been selected from the dropdown, activate button
    if region_1_id != "" and region_2_id != "" and region_3_id != "":
        return "Delete some structures to select new ones", True

    if region_1_id != "" or region_2_id != "" or region_3_id != "":
        return "Please choose a structure above", True

    return dash.no_update


# Function to update label of the add lipid button
@app.app.callback(
    Output("page-4-add-lipid-button", "children"),
    Output("page-4-add-lipid-button", "disabled"),
    Input("page-4-toast-lipid-1", "header"),
    Input("page-4-toast-lipid-2", "header"),
    Input("page-4-toast-lipid-3", "header"),
    State("page-4-dropdown-lipid-names", "value"),
    State("page-4-dropdown-lipid-structures", "value"),
    Input("page-4-dropdown-lipid-cations", "value"),
)
def page_4_click(header_1, header_2, header_3, name, structure, cation):
    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    # if at least one headers is free
    if header_1 == "" or header_2 == "" or header_3 == "":

        if cation is not None and cation != "":
            # Get lipid name
            lipid_string = name + " " + structure + " " + cation

            # Compare to existing headers
            if lipid_string not in [header_1, header_2, header_3]:

                return "Add " + lipid_string + " to selection", False

            else:
                return "Please choose a lipid that hasn't been selected yet", True

    return "Please choose a lipid above", True


# # Function to update label of the add structure button
# @app.app.callback(
#     Output("page-4-compare-structure-button", "disabled"),
#     # Output("page-4-compare-structure-button", "className"),
#     Input("page-4-selected-region-1", "data"),
#     Input("page-4-selected-region-2", "data"),
#     Input("page-4-selected-region-3", "data"),
# )
# def page_4_click(region_1_id, region_2_id, region_3_id):

#     # Find out which input triggered the function
#     id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

#     # If lipids has been selected from the dropdown, activate button
#     if (
#         (region_1_id != "" and region_2_id != "")
#         or (region_1_id != "" and region_3_id != "")
#         or (region_2_id != "" and region_3_id != "")
#     ):
#         return False
#         # return "mt-5"

#     return True
#     # return "d-none"


# Function to add region choice to selection
@app.app.callback(
    Output("page-4-toast-region-1", "header"),
    Output("page-4-toast-region-2", "header"),
    Output("page-4-toast-region-3", "header"),
    Output("page-4-selected-region-1", "data"),
    Output("page-4-selected-region-2", "data"),
    Output("page-4-selected-region-3", "data"),
    Output("page-4-toast-region-1", "is_open"),
    Output("page-4-toast-region-2", "is_open"),
    Output("page-4-toast-region-3", "is_open"),
    Output("page-4-last-selected-regions", "data"),
    Input("page-4-add-structure-button", "n_clicks"),
    Input("page-4-toast-region-1", "is_open"),
    Input("page-4-toast-region-2", "is_open"),
    Input("page-4-toast-region-3", "is_open"),
    State("page-4-selected-region-1", "data"),
    State("page-4-selected-region-2", "data"),
    State("page-4-selected-region-3", "data"),
    State("page-4-toast-region-1", "header"),
    State("page-4-toast-region-2", "header"),
    State("page-4-toast-region-3", "header"),
    State("page-4-last-selected-regions", "data"),
    State("page-4-add-structure-button", "children"),
)
def page_4_add_toast_region_selection(
    clicked_add,
    bool_toast_1,
    bool_toast_2,
    bool_toast_3,
    region_1_id,
    region_2_id,
    region_3_id,
    header_1,
    header_2,
    header_3,
    l_selected_regions,
    label_region,
):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]

    if len(id_input) == 0:
        return "", "", "", "", "", "", False, False, False, []

    # If a region has been deleted from a toast
    if value_input == "is_open":

        # Delete corressponding header and index
        if id_input == "page-4-toast-region-1":
            header_1 = ""
            l_selected_regions.remove(region_1_id)
            region_1_id = ""

        elif id_input == "page-4-toast-region-2":
            header_2 = ""
            l_selected_regions.remove(region_2_id)
            region_2_id = ""

        elif id_input == "page-4-toast-region-3":
            header_3 = ""
            l_selected_regions.remove(region_3_id)
            l_region_3_index = ""
        else:
            logging.warning("BUG in page_2_add_dropdown_selection")

        return (
            header_1,
            header_2,
            header_3,
            region_1_id,
            region_2_id,
            region_3_id,
            bool_toast_1,
            bool_toast_2,
            bool_toast_3,
            l_selected_regions,
        )

    # Otherwise, add region to selection
    elif id_input == "page-4-add-structure-button":
        if label_region != "Please choose a structure above":
            region = label_region.split("Add ")[1].split(" to selection")[0]
            region_id = atlas.dic_name_acronym[region]
            if region_id not in l_selected_regions:
                l_selected_regions.append(region_id)

                # Check first slot available
                if not bool_toast_1:
                    header_1 = region
                    region_1_id = region_id
                    bool_toast_1 = True
                elif not bool_toast_2:
                    header_2 = region
                    region_2_id = region_id
                    bool_toast_2 = True
                elif not bool_toast_3:
                    header_3 = region
                    region_3_id = region_id
                    bool_toast_3 = True
                else:
                    logging.warning("BUG, more than 3 regions have been selected")
                    return dash.no_update

                return (
                    header_1,
                    header_2,
                    header_3,
                    region_1_id,
                    region_2_id,
                    region_3_id,
                    bool_toast_1,
                    bool_toast_2,
                    bool_toast_3,
                    l_selected_regions,
                )

    return dash.no_update


# ! Need to have lipids that have been MAIA transformed only in page-4-toast-lipid-1, page-4-toast-lipid-2 etc
# ! Maybe remove the possibility to have more than 1 lipid?
# Function to plot page-4-graph-volume when its state get updated
@app.app.callback(
    Output("page-4-graph-volume", "figure"),
    Input("page-4-selected-lipid-1", "data"),
    Input("page-4-selected-lipid-2", "data"),
    Input("page-4-selected-lipid-3", "data"),
    Input("page-4-display-button", "n_clicks"),
    State("page-4-toast-lipid-1", "header"),
    State("page-4-toast-lipid-2", "header"),
    State("page-4-toast-lipid-3", "header"),
    State("page-4-last-selected-regions", "data"),
    State("page-4-selected-region-1", "data"),
    State("page-4-selected-region-2", "data"),
    State("page-4-selected-region-3", "data"),
)
def page_4_plot_graph_volume(
    l_lipid_1_index,
    l_lipid_2_index,
    l_lipid_3_index,
    n_clicks_button_display,
    name_lipid_1,
    name_lipid_2,
    name_lipid_3,
    l_selected_regions,
    name_region_1,
    name_region_2,
    name_region_3,
):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]

    # Compute set of ids for the volume plot if it is going to be plotted
    if id_input == "page-4-display-button":
        set_id = set([])
        for acronym in l_selected_regions:
            set_id = set_id.union(atlas.dic_acronym_children_id[acronym])
        # if len(set_id) < 5:
        #     decrease_resolution_factor = 3
        # elif len(set_id) < 10:
        #     decrease_resolution_factor = 4
        # elif len(set_id) < 50:
        #     decrease_resolution_factor = 5
        # elif len(set_id) < 100:
        #     decrease_resolution_factor = 6
        # else:
        #     decrease_resolution_factor = 7
        # # If no region was selected, put them all
        if len(set_id) == 0:
            set_id = None
            # decrease_resolution_factor = 7

        # Set the default decrease_resolution_factor to 6, regardless of the number of regions
        decrease_resolution_factor = 6
        logging.info(
            "For the computation of 3D volume, decrease_resolution_factor is "
            + str(decrease_resolution_factor)
        )

    # If a lipid selection has been done
    if id_input == "page-4-display-button":

        if (
            np.sum(l_lipid_1_index) > -app.data.get_slice_number()
            or np.sum(l_lipid_2_index) > -app.data.get_slice_number()
            or np.sum(l_lipid_3_index) > -app.data.get_slice_number()
        ):
            # Build the list of mz boundaries for each peak and each index
            lll_lipid_bounds = [
                [
                    [
                        (
                            float(app.data.get_annotations().iloc[index]["min"]),
                            float(app.data.get_annotations().iloc[index]["max"]),
                        )
                    ]
                    if index != -1
                    else None
                    for index in [lipid_1_index, lipid_2_index, lipid_3_index]
                ]
                for lipid_1_index, lipid_2_index, lipid_3_index in zip(
                    l_lipid_1_index, l_lipid_2_index, l_lipid_3_index
                )
            ]

            return figures.compute_3D_volume_figure(
                ll_t_bounds=lll_lipid_bounds,
                name_lipid_1=name_lipid_1,
                name_lipid_2=name_lipid_2,
                name_lipid_3=name_lipid_3,
                set_id_regions=set_id,
                decrease_dimensionality_factor=decrease_resolution_factor,
                cache_flask=cache_flask,
            )

        else:
            # probably the page has just been loaded, so do nothing
            return dash.no_update

    return dash.no_update


# Function to plot page-4-graph-heatmap
@app.app.long_callback(
    output=Output("page-4-graph-heatmap", "figure"),
    inputs=[
        Input("page-4-compare-structure-button", "n_clicks"),
        Input("page-4-slider-percentile", "value"),
        State("page-4-last-selected-regions", "data"),
        State("page-4-selected-region-1", "data"),
        State("page-4-selected-region-2", "data"),
        State("page-4-selected-region-3", "data"),
    ],
    running=[
        # (Output("page-4-compare-structure-button", "disabled"), True, False),
        (Output("page-4-progress-bar-structure", "className"), "", "d-none",),
        (Output("page-4-graph-heatmap", "className"), "d-none", ""),
        (Output("page-4-slider-percentile", "className"), "d-none", ""),
    ],
    progress=[
        Output("page-4-progress-bar-structure", "value"),
        Output("page-4-progress-bar-structure", "label"),
    ],
    prevent_initial_call=True,
    cache_args_to_ignore=[0, 2],
)
def page_4_plot_graph_heatmap_mz_selection(
    set_progress,
    n_clicks_button_display,
    percentile,
    l_selected_regions,
    name_region_1,
    name_region_2,
    name_region_3,
):

    # sections = [{"value": 10, "color": "red"}]
    set_progress((0, "Inspecting dataset..."))

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]

    # case structures have been selected
    if id_input == "page-4-compare-structure-button" or id_input == "page-4-slider-percentile":
        if len(l_selected_regions) > 1:
            return figures.compute_clustergram_figure(
                set_progress, cache_flask, l_selected_regions, percentile=percentile
            )
    return dash.no_update


# Function to refine dropdown names choices
@app.app.callback(
    Output("page-4-dropdown-lipid-names", "data"),
    Output("page-4-dropdown-lipid-structures", "data"),
    Output("page-4-dropdown-lipid-cations", "data"),
    Output("page-4-dropdown-lipid-names", "value"),
    Output("page-4-dropdown-lipid-structures", "value"),
    Output("page-4-dropdown-lipid-cations", "value"),
    Input("page-4-dropdown-lipid-names", "value"),
    Input("page-4-dropdown-lipid-structures", "value"),
    State("page-4-dropdown-lipid-names", "data"),
    State("page-4-dropdown-lipid-structures", "data"),
    State("page-4-dropdown-lipid-cations", "data"),
)
def page_2bis_handle_dropdowns(name, structure, options_names, options_structures, options_cations):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    # Refine dropdown hierarchically: when first one is set, the 2 other options are computed accordingly,
    # when second one is set, the last one option is computed

    if len(id_input) == 0 or id_input == "dcc-store-slice-index":
        options_names = [
            {"label": name, "value": name}
            for name in sorted(app.data.get_annotations().name.unique())
        ]
        return options_names, [], [], None, None, None

    elif name is not None:
        if id_input == "page-4-dropdown-lipid-names":
            structures = app.data.get_annotations()[
                app.data.get_annotations()["name"] == name
            ].structure.unique()
            options_structures = [
                {"label": structure, "value": structure} for structure in sorted(structures)
            ]
            return options_names, options_structures, [], name, None, None

        elif structure is not None:
            if id_input == "page-4-dropdown-lipid-structures":
                cations = app.data.get_annotations()[
                    (app.data.get_annotations()["name"] == name)
                    & (app.data.get_annotations()["structure"] == structure)
                ].cation.unique()
                options_cations = [{"label": cation, "value": cation} for cation in sorted(cations)]
                return options_names, options_structures, options_cations, name, structure, None

    return dash.no_update


# Function to add dropdown choice to selection
@app.app.callback(
    Output("page-4-toast-lipid-1", "header"),
    Output("page-4-toast-lipid-2", "header"),
    Output("page-4-toast-lipid-3", "header"),
    Output("page-4-selected-lipid-1", "data"),
    Output("page-4-selected-lipid-2", "data"),
    Output("page-4-selected-lipid-3", "data"),
    Output("page-4-toast-lipid-1", "is_open"),
    Output("page-4-toast-lipid-2", "is_open"),
    Output("page-4-toast-lipid-3", "is_open"),
    Output("page-4-last-selected-lipids", "data"),
    State("page-4-dropdown-lipid-cations", "value"),
    Input("page-4-add-lipid-button", "n_clicks"),
    Input("page-4-toast-lipid-1", "is_open"),
    Input("page-4-toast-lipid-2", "is_open"),
    Input("page-4-toast-lipid-3", "is_open"),
    State("page-4-dropdown-lipid-names", "value"),
    State("page-4-dropdown-lipid-structures", "value"),
    State("page-4-selected-lipid-1", "data"),
    State("page-4-selected-lipid-2", "data"),
    State("page-4-selected-lipid-3", "data"),
    State("page-4-toast-lipid-1", "header"),
    State("page-4-toast-lipid-2", "header"),
    State("page-4-toast-lipid-3", "header"),
    State("page-4-last-selected-lipids", "data"),
)
def page_2bis_add_toast_selection(
    cation,
    n_clicks,
    bool_toast_1,
    bool_toast_2,
    bool_toast_3,
    name,
    structure,
    l_lipid_1_index,
    l_lipid_2_index,
    l_lipid_3_index,
    header_1,
    header_2,
    header_3,
    l_selected_lipids,
):

    # ! Make lipid selection more natural, when limited to one lipid

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]

    empty_lipid_list = [-1 for i in range(app.data.get_slice_number())]
    # Take advantage of dash bug that automatically triggers 'page-4-dropdown-lipid-cations'
    # everytime the page is loaded, and prevent using dcc-store-slice-index as an input
    # if page-4-dropdown-lipid-cations is called while there's no lipid name defined, it means the page just got loaded
    if len(id_input) == 0 or (id_input == "page-4-dropdown-lipid-cations" and name is None):
        return (
            "",
            "",
            "",
            empty_lipid_list,
            empty_lipid_list,
            empty_lipid_list,
            False,
            False,
            False,
            [],
        )

    # If a lipid has been deleted from a toast
    if value_input == "is_open":

        # Delete corressponding header and index
        if id_input == "page-4-toast-lipid-1":
            header_1 = ""
            l_selected_lipids.remove(l_lipid_1_index[0])
            l_lipid_1_index = empty_lipid_list

        elif id_input == "page-4-toast-lipid-2":
            header_2 = ""
            l_selected_lipids.remove(l_lipid_2_index[0])
            l_lipid_2_index = empty_lipid_list

        elif id_input == "page-4-toast-lipid-3":
            header_3 = ""
            l_selected_lipids.remove(l_lipid_3_index[0])
            l_lipid_3_index = empty_lipid_list
        else:
            logging.warning("BUG in page_2_add_dropdown_selection")

        return (
            header_1,
            header_2,
            header_3,
            l_lipid_1_index,
            l_lipid_2_index,
            l_lipid_3_index,
            bool_toast_1,
            bool_toast_2,
            bool_toast_3,
            l_selected_lipids,
        )

    # Otherwise, add lipid to selection
    elif cation is not None and id_input == "page-4-add-lipid-button":

        for slice_index in range(app.data.get_slice_number()):

            # Find lipid location
            l_lipid_loc = (
                app.data.get_annotations()
                .index[
                    (app.data.get_annotations()["name"] == name)
                    & (app.data.get_annotations()["structure"] == structure)
                    & (app.data.get_annotations()["slice"] == slice_index + 1)
                    & (app.data.get_annotations()["cation"] == cation)
                ]
                .tolist()
            )
            # If several lipids correspond to the selection, we have a problem...
            if len(l_lipid_loc) > 1:
                logging.warning("More than one lipid corresponds to the selection")
                l_lipid_loc = [l_lipid_loc[-1]]
            if len(l_lipid_loc) == 0:
                l_lipid_loc = [-1]

            lipid_string = name + " " + structure + " " + cation

            if slice_index == 0:
                l_selected_lipids.append(l_lipid_loc[0])

            # Check first slot available
            if not bool_toast_1:
                header_1 = lipid_string
                l_lipid_1_index[slice_index] = l_lipid_loc[0]
                if slice_index == app.data.get_slice_number() - 1:
                    bool_toast_1 = True
            elif not bool_toast_2:
                header_2 = lipid_string
                l_lipid_2_index[slice_index] = l_lipid_loc[0]
                if slice_index == app.data.get_slice_number() - 1:
                    bool_toast_2 = True
            elif not bool_toast_3:
                header_3 = lipid_string
                l_lipid_3_index[slice_index] = l_lipid_loc[0]
                if slice_index == app.data.get_slice_number() - 1:
                    bool_toast_3 = True
            else:
                logging.warning("BUG, more than 3 lipids have been selected")
                return dash.no_update

        return (
            header_1,
            header_2,
            header_3,
            l_lipid_1_index,
            l_lipid_2_index,
            l_lipid_3_index,
            bool_toast_1,
            bool_toast_2,
            bool_toast_3,
            l_selected_lipids,
        )

    return dash.no_update


# Function to disable/enable dropdowns depending on the number of lipids selected
@app.app.callback(
    Output("page-4-dropdown-lipid-names", "disabled"),
    Output("page-4-dropdown-lipid-structures", "disabled"),
    Output("page-4-dropdown-lipid-cations", "disabled"),
    # Output("page-4-warning-lipids-number", "className"),
    Input("page-4-selected-lipid-1", "data"),
    Input("page-4-selected-lipid-2", "data"),
    Input("page-4-selected-lipid-3", "data"),
)
def page_4_disable_dropdowns(l_lipid_1_index, l_lipid_2_index, l_lipid_3_index):

    # If all slots are taken, disable all dropdowns
    if (
        np.sum(l_lipid_1_index) > -app.data.get_slice_number()
        and np.sum(l_lipid_2_index) > -app.data.get_slice_number()
        and np.sum(l_lipid_3_index) > -app.data.get_slice_number()
    ):
        return True, True, True  # , "mt-1 text-center"
    else:
        return False, False, False  # , "mt-1 text-center d-none"


@app.app.callback(
    Output("page-4-display-button", "disabled"),
    Output("page-4-compare-structure-button", "disabled"),
    Input("page-4-selected-lipid-1", "data"),
    Input("page-4-selected-lipid-2", "data"),
    Input("page-4-selected-lipid-3", "data"),
    Input("page-4-selected-region-1", "data"),
    Input("page-4-selected-region-2", "data"),
    Input("page-4-selected-region-3", "data"),
)
def page_2_active_display(
    l_lipid_1_index, l_lipid_2_index, l_lipid_3_index, region_1_id, region_2_id, region_3_id
):

    # If two structure
    if (
        (region_1_id != "" and region_2_id != "")
        or (region_1_id != "" and region_3_id != "")
        or (region_2_id != "" and region_3_id != "")
    ):

        # If at least one lipid:
        if (
            np.sum(l_lipid_1_index + l_lipid_2_index + l_lipid_3_index)
            > -3 * app.data.get_slice_number()
        ):
            return False, False
        else:
            return True, False

    # If one structure
    if region_1_id != "" or region_2_id != "" or region_3_id != "":
        # If at least one lipid:
        if (
            np.sum(l_lipid_1_index + l_lipid_2_index + l_lipid_3_index)
            > -3 * app.data.get_slice_number()
        ):
            return False, True

        else:
            return True, True

    return True, True


@app.app.callback(
    Output("page-4-modal-volume", "is_open"),
    Input("page-4-display-button", "n_clicks"),
    [State("page-4-modal-volume", "is_open")],
)
def toggle_modal(n1, is_open):
    if n1:
        return not is_open
    return is_open


@app.app.callback(
    Output("page-4-modal-heatmap", "is_open"),
    Input("page-4-compare-structure-button", "n_clicks"),
    [State("page-4-modal-heatmap", "is_open")],
)
def toggle_modal(n1, is_open):
    if n1:
        return not is_open
    return is_open

