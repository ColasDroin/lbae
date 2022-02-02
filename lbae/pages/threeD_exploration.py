###### IMPORT MODULES ######

# Official modules
import dash_bootstrap_components as dbc
from dash import dcc, html
import logging
import dash_draggable
from dash.dependencies import Input, Output, State
import numpy as np
import dash

# Data module
from lbae.app import figures, atlas
from lbae import app
from lbae.modules.tools.misc import return_pickled_object

###### DEFFINE PAGE LAYOUT ######


def return_layout(basic_config, slice_index):

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
                    {"i": "page-4-card-region-selection", "x": 0, "y": 0, "w": 8, "h": 20},
                    {"i": "page-4-card-lipid-selection", "x": 8, "y": 0, "w": 4, "h": 11},
                    {"i": "page-4-card-range-selection", "x": 8, "y": 8, "w": 4, "h": 6},
                    {"i": "page-4-card-input-selection", "x": 8, "y": 10, "w": 4, "h": 3},
                    {"i": "page-4-card-main-graph", "x": 0, "y": 20, "w": 12, "h": 32},
                ],
                "md": [
                    {"i": "page-4-card-region-selection", "x": 0, "y": 0, "w": 7, "h": 14},
                    {"i": "page-4-card-lipid-selection", "x": 6, "y": 0, "w": 3, "h": 12},
                    {"i": "page-4-card-range-selection", "x": 6, "y": 8, "w": 3, "h": 6},
                    {"i": "page-4-card-input-selection", "x": 6, "y": 10, "w": 3, "h": 3},
                    {"i": "page-4-card-main-graph", "x": 0, "y": 14, "w": 10, "h": 14},
                ],
                "sm": [
                    {"i": "page-4-card-region-selection", "x": 0, "y": 0, "w": 6, "h": 19},
                    {"i": "page-4-card-lipid-selection", "x": 0, "y": 19, "w": 6, "h": 11},
                    {"i": "page-4-card-range-selection", "x": 0, "y": 19 + 7, "w": 6, "h": 5},
                    {"i": "page-4-card-input-selection", "x": 0, "y": 19 + 7 + 5, "w": 6, "h": 3},
                    {"i": "page-4-card-main-graph", "x": 0, "y": 19, "w": 6, "h": 19},
                ],
                "xs": [
                    {"i": "page-4-card-region-selection", "x": 0, "y": 0, "w": 4, "h": 14},
                    {"i": "page-4-card-lipid-selection", "x": 0, "y": 0, "w": 4, "h": 11},
                    {"i": "page-4-card-range-selection", "x": 0, "y": 14 + 7, "w": 4, "h": 5},
                    {"i": "page-4-card-input-selection", "x": 0, "y": 14 + 7 + 5, "w": 4, "h": 3},
                    {"i": "page-4-card-main-graph", "x": 0, "y": 14, "w": 4, "h": 14},
                ],
                "xxs": [
                    {"i": "page-4-card-region-selection", "x": 0, "y": 0, "w": 2, "h": 9},
                    {"i": "page-4-card-lipid-selection", "x": 0, "y": 0, "w": 2, "h": 10},
                    {"i": "page-4-card-range-selection", "x": 0, "y": 9 + 7, "w": 2, "h": 5},
                    {"i": "page-4-card-input-selection", "x": 0, "y": 9 + 7 + 5, "w": 2, "h": 3},
                    {"i": "page-4-card-main-graph", "x": 0, "y": 9, "w": 2, "h": 9},
                ],
            },
            children=[
                dbc.Card(
                    id="page-4-card-region-selection",
                    style={"width": "100%", "height": "100%"},
                    children=[
                        dbc.CardHeader(children="Structure selection",),
                        dbc.CardBody(
                            className="py-0 mb-0 mt-2",
                            children=[
                                dbc.Spinner(
                                    color="dark",
                                    show_initially=False,
                                    children=[
                                        html.Div(
                                            # className="page-1-fixed-aspect-ratio",
                                            children=[
                                                dcc.Graph(
                                                    id="page-4-graph-region-selection",
                                                    config=basic_config,
                                                    # style={
                                                    #    "width": "100%",
                                                    #    "height": "100%",
                                                    #    "position": "absolute",
                                                    #    "left": "0",
                                                    # },
                                                    figure=return_pickled_object(
                                                        "figures/atlas_page/3D",
                                                        "treemaps",
                                                        force_update=True,
                                                        compute_function=figures.compute_treemaps_figure,
                                                    ),
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                dbc.ButtonGroup(
                                    className="d-flex justify-content-center",
                                    children=[
                                        dbc.Button(
                                            children="Please choose a structure above",
                                            id="page-4-add-structure-button",
                                            className="mt-1",
                                            color="primary",
                                            disabled=True,
                                            # block=True,
                                        ),
                                    ],
                                ),
                                # Wrap toasts in div to prevent their expansion
                                dbc.Toast(
                                    id="page-4-toast-region-1",
                                    header="name-region-1",
                                    icon="primary",
                                    dismissable=True,
                                    is_open=False,
                                    bodyClassName="p-0",
                                    className="mt-3",
                                    style={"margin": "auto"},
                                ),
                                dbc.Toast(
                                    id="page-4-toast-region-2",
                                    header="name-region-2",
                                    icon="primary",
                                    dismissable=True,
                                    is_open=False,
                                    bodyClassName="p-0",
                                    className="mt-1",
                                    style={"margin": "auto"},
                                ),
                                dbc.Toast(
                                    id="page-4-toast-region-3",
                                    header="name-region-3",
                                    icon="primary",
                                    dismissable=True,
                                    is_open=False,
                                    bodyClassName="p-0",
                                    className="mt-1",
                                    style={"margin": "auto"},
                                ),
                                # html.Div("‎‎‏‏‎ ‎"),  # Empty span to prevent toast from bugging
                            ],
                        ),
                    ],
                ),
                dbc.Card(
                    style={"maxWidth": "100%", "margin": "0 auto", "width": "100%", "height": "100%"},
                    id="page-4-card-lipid-selection",
                    children=[
                        dbc.CardHeader(children="Lipid selection"),
                        dbc.CardBody(
                            className="pt-1",
                            children=[
                                dbc.Tooltip(
                                    children="Please select the lipids of your choice (up to three):",
                                    target="page-4-card-lipid-selection",
                                    placement="left",
                                ),
                                # Dropdown must be wrapped in div, otherwise lazy loading creates bug with tooltips
                                html.Div(
                                    id="page-4-div-dropdown-lipid-names",
                                    children=[
                                        dcc.Dropdown(id="page-4-dropdown-lipid-names", options=[], multi=False,),
                                    ],
                                ),
                                dbc.Tooltip(
                                    children="Choose the category of your lipid",
                                    target="page-4-div-dropdown-lipid-names",
                                    placement="left",
                                ),
                                html.Div(
                                    id="page-4-div-dropdown-lipid-structures",
                                    children=[
                                        dcc.Dropdown(
                                            id="page-4-dropdown-lipid-structures",
                                            options=[],
                                            multi=False,
                                            className="mt-2",
                                        ),
                                    ],
                                ),
                                dbc.Tooltip(
                                    children="After choosing the lipid category, choose the structure of your lipid",
                                    target="page-4-div-dropdown-lipid-structures",
                                    placement="left",
                                ),
                                html.Div(
                                    id="page-4-div-dropdown-lipid-cations",
                                    children=[
                                        dcc.Dropdown(
                                            id="page-4-dropdown-lipid-cations",
                                            options=[],
                                            multi=False,
                                            className="mt-2",
                                        ),
                                    ],
                                ),
                                dbc.Tooltip(
                                    children="After choosing the lipid structure, choose the cation binded to your lipid",
                                    target="page-4-div-dropdown-lipid-cations",
                                    placement="left",
                                ),
                                # Wrap toasts in div to prevent their expansion
                                dbc.Toast(
                                    id="page-4-toast-lipid-1",
                                    header="name-lipid-1",
                                    icon="primary",
                                    dismissable=True,
                                    is_open=False,
                                    bodyClassName="p-0",
                                    className="mt-3",
                                    style={"margin": "auto"},
                                ),
                                dbc.Toast(
                                    id="page-4-toast-lipid-2",
                                    header="name-lipid-2",
                                    icon="primary",
                                    dismissable=True,
                                    is_open=False,
                                    bodyClassName="p-0",
                                    className="mt-1",
                                    style={"margin": "auto"},
                                ),
                                dbc.Toast(
                                    id="page-4-toast-lipid-3",
                                    header="name-lipid-3",
                                    icon="primary",
                                    dismissable=True,
                                    is_open=False,
                                    bodyClassName="p-0",
                                    className="mt-1",
                                    style={"margin": "auto"},
                                ),
                                html.Div(
                                    id="page-4-warning-lipids-number",
                                    className="text-center mt-1",
                                    children=html.Strong(
                                        children="Please delete some lipids to choose new ones.",
                                        style={"color": "#df5034"},
                                    ),
                                ),
                                dbc.ButtonGroup(
                                    className="d-flex justify-content-center",
                                    children=[
                                        dbc.Button(
                                            children="Display",
                                            id="page-4-display-button",
                                            className="mt-1",
                                            color="primary",
                                            disabled=True,
                                            # block=True,
                                        ),
                                    ],
                                ),
                                # dcc.Download(id="page-4-download-data"),
                            ],
                        ),
                    ],
                ),
                dbc.Card(
                    style={"maxWidth": "100%", "margin": "0 auto", "width": "100%", "height": "100%"},
                    # className="mt-4",
                    id="page-4-card-range-selection",
                    children=[
                        dbc.CardHeader("Range selection"),
                        dbc.CardBody(
                            className="pt-1",
                            children=[
                                html.Small(
                                    children="Please enter the lower and upper bounds of your m/z range selection.",
                                    className="text-center",
                                    id="page-4-text-bounds",
                                ),
                                dbc.Tooltip(
                                    children="Your selection can't exceed a range of 10m/z, and must be comprised in-between 400 and 1200.",
                                    target="page-4-text-bounds",
                                    placement="left",
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.Input(id="page-4-lower-bound", placeholder="Lower bound (m/z value)",),
                                        dbc.Input(id="page-4-upper-bound", placeholder="Upper bound (m/z value)",),
                                        # dbc.InputGroupAddon(
                                        dbc.Button("Display", id="page-4-button-bounds", n_clicks=0, color="primary",),
                                        #    addon_type="prepend",
                                        # ),
                                    ],
                                    size="sm",
                                ),
                                html.Small(
                                    children="Or choose a m/z value with a given range.",
                                    className="text-center",
                                    id="page-4-text-range",
                                ),
                                dbc.Tooltip(
                                    children="Your selection can't exceed a range of 10m/z, and must be comprised in-between 400 and 1200.",
                                    target="page-4-text-range",
                                    placement="left",
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.Input(id="page-4-mz-value", placeholder="m/z value"),
                                        dbc.Input(id="page-4-mz-range", placeholder="Range"),
                                        # dbc.InputGroupAddon(
                                        dbc.Button("Display", id="page-4-button-range", n_clicks=0, color="primary",),
                                        #    addon_type="prepend",
                                        # ),
                                    ],
                                    size="sm",
                                ),
                            ],
                        ),
                    ],
                ),
                dbc.Card(
                    style={"maxWidth": "100%", "margin": "0 auto", "width": "100%", "height": "100%"},
                    id="page-4-card-input-selection",
                    children=[
                        dbc.CardHeader("Input selection"),
                        dbc.CardBody(
                            className="pt-0 mt-3",
                            children=[
                                dbc.RadioItems(
                                    options=[
                                        {"label": "Lipid selection", "value": 1},
                                        {"label": "m/z boundaries", "value": 2},
                                        {"label": "m/z range", "value": 3},
                                    ],
                                    value=1,
                                    id="page-4-radioitems-input",
                                    inline=True,
                                    # className="pb-1 mt-0 pt-0",
                                ),
                            ],
                        ),
                    ],
                ),
                dbc.Card(
                    id="page-4-card-main-graph",
                    className="no-transition",
                    style={"width": "100%", "height": "100%"},
                    children=[
                        dbc.CardHeader(
                            className="d-flex",
                            children="Lipid selection interpolated in 3D",
                            # [
                            #     dbc.Tabs(
                            #         [
                            #             dbc.Tab(label="TIC per slice in 3D", tab_id="page-4-tab-1"),
                            #             # dbc.Tab(label="Lipid selection per slice in 3D", tab_id="page-4-tab-3"),
                            #             dbc.Tab(label="Lipid selection interpolated in 3D", tab_id="page-4-tab-4"),
                            #         ],
                            #         id="page-4-card-tabs",
                            #         active_tab="page-4-tab-4",
                            #     ),
                            # ],
                        ),
                        dbc.CardBody(
                            className="py-0 mb-0 mt-2",
                            children=[
                                dbc.Spinner(
                                    color="dark",
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
                                                    id="page-4-graph-heatmap-mz-selection",
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
                                                        "height": "95%",
                                                        "position": "absolute",
                                                        "left": "0",
                                                    },
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                html.Div("‎‎‏‏‎ ‎"),  # Empty span to prevent toast from bugging
                            ],
                        ),
                    ],
                ),
            ],
        ),
    )

    return page


###### APP CALLBACKS ######

# Function to make visible the alert regarding the plot page 4
@app.app.callback(
    Output("page-4-alert", "style"),
    Output("page-4-graph-heatmap-mz-selection", "style"),
    Input("page-4-display-button", "n_clicks"),
    # Input("page-4-card-tabs", "active_tab"),
    Input("page-4-radioitems-input", "value"),
    State("page-4-last-selected-lipids", "data"),
)
def page_4_display_alert(clicked_compute, input, l_lipids):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    # if id_input is None:
    #    return {}, {"display": "none"}

    # if active_tab == "page-4-tab-1":
    #     return (
    #         {"display": "none"},
    #         {"width": "100%", "height": "100%", "position": "absolute", "left": "0",},
    #     )

    # TODO : add the need to have the text field of the input range filled
    # elif (active_tab == "page-4-tab-3" or active_tab == "page-4-tab-4") and (
    #     (input == 1 and len(l_lipids) > 0) or input == 2 or input == 3
    # ):
    if (input == 1 and len(l_lipids) > 0) or input == 2 or input == 3:
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
                # acronym = atlas.dic_name_id[label]
                # print("New 3d figure loading: ", label, acronym)
                return "Add " + label + " to selection", False
        return "Please choose a structure above", True

    # If lipids has been selected from the dropdown, activate button
    if region_1_id != "" and region_2_id != "" and region_3_id != "":
        return "Delete some structures to select new ones", True

    if region_1_id != "" or region_2_id != "" or region_3_id != "":
        return "Please choose a structure above", True

    return dash.no_update


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
            print("BUG in tab_2_add_dropdown_selection")

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
            region_id = atlas.dic_name_id[region]
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
                    print("BUG, more than 3 regions have been selected")
                    return dash.no_update

                print("ici", l_selected_regions)

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


# Function to plot page-4-graph-heatmap-mz-selection when its state get updated
@app.app.callback(
    Output("page-4-graph-heatmap-mz-selection", "figure"),
    Output("page-4-radioitems-input", "value"),
    # Input("page-4-card-tabs", "active_tab"),
    Input("boundaries-high-resolution-mz-plot", "data"),
    Input("boundaries-low-resolution-mz-plot", "data"),
    Input("page-4-selected-lipid-1", "data"),
    Input("page-4-selected-lipid-2", "data"),
    Input("page-4-selected-lipid-3", "data"),
    Input("page-4-button-range", "n_clicks"),
    Input("page-4-button-bounds", "n_clicks"),
    Input("page-4-display-button", "n_clicks"),
    Input("page-4-radioitems-input", "value"),
    State("page-4-lower-bound", "value"),
    State("page-4-upper-bound", "value"),
    State("page-4-mz-value", "value"),
    State("page-4-mz-range", "value"),
    State("page-4-toast-lipid-1", "header"),
    State("page-4-toast-lipid-2", "header"),
    State("page-4-toast-lipid-3", "header"),
)
def page_2bis_plot_graph_heatmap_mz_selection(
    # active_tab,
    bound_high_res,
    bound_low_res,
    l_lipid_1_index,
    l_lipid_2_index,
    l_lipid_3_index,
    n_clicks_button_range,
    n_clicks_button_bounds,
    n_clicks_button_display,
    input,
    lb,
    hb,
    mz,
    mz_range,
    name_lipid_1,
    name_lipid_2,
    name_lipid_3,
):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]

    # case a mz value and a manual range have been inputed
    if id_input == "page-4-button-range" or (id_input == "page-4-radioitems-input" and value_input == 3):
        if mz is not None and mz_range is not None:
            mz = float(mz)
            mz_range = float(mz_range)
            if mz > 400 and mz < 1200 and mz_range < 10:
                return (
                    figures.compute_3D_volume_figure(
                        [[[(mz - mz_range / 2, mz + mz_range / 2)], None, None]] * app.data.get_slice_number()
                    ),
                    3,
                )

        return dash.no_update

    # case a two mz bounds values have been inputed
    elif id_input == "page-4-button-bounds" or (id_input == "page-4-radioitems-input" and value_input == 2):
        if lb is not None and hb is not None:
            lb, hb = float(lb), float(hb)
            if lb > 400 and hb < 1200 and hb - lb > 0 and hb - lb < 10:
                return figures.compute_3D_volume_figure([[[(lb, hb)], None, None]] * app.data.get_slice_number()), 2
        return dash.no_update

    # If a lipid selection has been done
    elif (
        id_input == "page-4-display-button"
        # or (id_input == "page-4-card-tabs" and (active_tab == "page-4-tab-3" or active_tab == "page-4-tab-4"))
        or (id_input == "page-4-radioitems-input" and value_input == 1)
    ):

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

            # if active_tab == "page-4-tab-3":
            #     # ! There seems to be a bug where the figure is computed twice (the callback is repeated) but can't figure out why...
            #     # ! On hold for now as, most likely this figure won't be kept in the app
            #     return (
            #         return_pickled_object(
            #             "figures/3D_page",
            #             "scatter_3D_" + name_lipid_1 + "_" + name_lipid_2 + "_" + name_lipid_3,
            #             force_update=False,
            #             compute_function=figures.compute_figure_bubbles_3D,
            #             ignore_arguments_naming=True,
            #             ll_t_bounds=lll_lipid_bounds,
            #             normalize_independently=True,
            #             name_lipid_1=name_lipid_1,
            #             name_lipid_2=name_lipid_2,
            #             name_lipid_3=name_lipid_3,
            #         ),
            #         1,
            #     )

            return (
                return_pickled_object(
                    "figures/3D_page",
                    "volume_interpolated_3D_" + name_lipid_1 + "_" + name_lipid_2 + "_" + name_lipid_3,
                    force_update=False,
                    compute_function=figures.compute_3D_volume_figure,
                    ignore_arguments_naming=True,
                    ll_t_bounds=lll_lipid_bounds,
                    name_lipid_1=name_lipid_1,
                    name_lipid_2=name_lipid_2,
                    name_lipid_3=name_lipid_3,
                ),
                1,
            )

        else:
            # probably the page has just been loaded, so do nothing
            # return app.slice_store.getSlice(slice_index).return_heatmap(binary_string=False)
            return dash.no_update

    return dash.no_update


# Function to refine dropdown names choices
@app.app.callback(
    Output("page-4-dropdown-lipid-names", "options"),
    Output("page-4-dropdown-lipid-structures", "options"),
    Output("page-4-dropdown-lipid-cations", "options"),
    Output("page-4-dropdown-lipid-names", "value"),
    Output("page-4-dropdown-lipid-structures", "value"),
    Output("page-4-dropdown-lipid-cations", "value"),
    Input("page-4-dropdown-lipid-names", "value"),
    Input("page-4-dropdown-lipid-structures", "value"),
    State("page-4-dropdown-lipid-names", "options"),
    State("page-4-dropdown-lipid-structures", "options"),
    State("page-4-dropdown-lipid-cations", "options"),
)
def page_2bis_handle_dropdowns(name, structure, options_names, options_structures, options_cations):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    # Refine dropdown hierarchically: when first one is set, the 2 other options are computed accordingly,
    # when second one is set, the last one option is computed

    if len(id_input) == 0 or id_input == "dcc-store-slice-index":
        options_names = [{"label": name, "value": name} for name in sorted(app.data.get_annotations().name.unique())]
        return options_names, [], [], None, None, None

    elif name is not None:
        if id_input == "page-4-dropdown-lipid-names":
            structures = app.data.get_annotations()[app.data.get_annotations()["name"] == name].structure.unique()
            options_structures = [{"label": structure, "value": structure} for structure in sorted(structures)]
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
    Input("page-4-dropdown-lipid-cations", "value"),
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

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    value_input = dash.callback_context.triggered[0]["prop_id"].split(".")[1]

    empty_lipid_list = [-1 for i in range(app.data.get_slice_number())]
    # Take advantage of dash bug that automatically triggers 'page-4-dropdown-lipid-cations'
    # everytime the page is loaded, and prevent using dcc-store-slice-index as an input
    # if page-4-dropdown-lipid-cations is called while there's no lipid name defined, it means the page just got loaded
    if len(id_input) == 0 or (id_input == "page-4-dropdown-lipid-cations" and name is None):
        return "", "", "", empty_lipid_list, empty_lipid_list, empty_lipid_list, False, False, False, []

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
            print("BUG in tab_2_add_dropdown_selection")

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
    elif cation is not None and id_input == "page-4-dropdown-lipid-cations":

        for slice_index in range(app.data.get_slice_number()):

            # Find lipid location
            l_lipid_loc = (
                app.data.get_annotations()
                .index[
                    (app.data.get_annotations()["name"] == name)
                    & (app.data.get_annotations()["structure"] == structure)
                    & (app.data.get_annotations()["slice"] == slice_index)
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
                print("BUG, more than 3 lipids have been selected")
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
    Output("page-4-warning-lipids-number", "className"),
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
        return True, True, True, "mt-1 text-center"
    else:
        return False, False, False, "mt-1 text-center d-none"


@app.app.callback(
    Output("page-4-display-button", "disabled"),
    Input("page-4-selected-lipid-1", "data"),
    Input("page-4-selected-lipid-2", "data"),
    Input("page-4-selected-lipid-3", "data"),
)
def tab_2_active_display(l_lipid_1_index, l_lipid_2_index, l_lipid_3_index):
    # If lipids has been selected from the dropdown, activate button
    if np.sum(l_lipid_1_index + l_lipid_2_index + l_lipid_3_index) > -3 * app.data.get_slice_number():
        return False
    else:
        return True


@app.app.callback(
    Output("page-4-button-range", "disabled"), Input("page-4-mz-value", "value"), Input("page-4-mz-range", "value"),
)
def page_2bis_button_range(mz, mz_range):
    if mz is not None and mz_range is not None:
        mz = float(mz)
        mz_range = float(mz_range)
        if mz > 400 and mz < 1200 and mz_range < 10:
            return False
    return True


@app.app.callback(
    Output("page-4-button-bounds", "disabled"),
    Input("page-4-lower-bound", "value"),
    Input("page-4-upper-bound", "value"),
)
def page_2bis_button_window(lb, hb):
    if lb is not None and hb is not None:
        lb, hb = float(lb), float(hb)
        if lb > 400 and hb < 1200 and hb - lb > 0 and hb - lb < 10:
            return False
    return True

