###### IMPORT MODULES ######

# Official modules
import dash_bootstrap_components as dbc
from dash import dcc, html
import logging

# from dash.dependencies import Input, Output, State
import dash

# import orjson
from dash.dependencies import Input, Output, State
import numpy as np

# Data module
from lbae.app import figures
from lbae import app
from lbae.modules.tools.misc import return_pickled_object

###### DEFFINE PAGE LAYOUT ######


def return_layout(basic_config):

    page = html.Div(
        children=[
            ### First row
            dbc.Row(
                className="d-flex justify-content-center flex-wrap",
                justify="center",
                children=[
                    ## First column
                    dbc.Col(
                        md=6,
                        children=[
                            dbc.Card(
                                className="no-transition",
                                # style={"maxWidth": "100%", "margin": "0 auto"},
                                children=[
                                    dbc.CardHeader(
                                        id="page-2bis-toast-graph-heatmap-mz-selection",
                                        className="d-flex",
                                        children=[
                                            dbc.Tabs(
                                                [
                                                    dbc.Tab(label="TIC per slice in 3D", tab_id="page-2bis-tab-1"),
                                                    dbc.Tab(
                                                        label="Lipid selection per slice in 2D",
                                                        tab_id="page-2bis-tab-2",
                                                    ),
                                                    dbc.Tab(label="Lipid selection in 3D", tab_id="page-2bis-tab-3"),
                                                ],
                                                id="page-2bis-card-tabs",
                                                active_tab="page-2bis-tab-1",
                                            ),
                                        ],
                                    ),
                                    dbc.CardBody(
                                        className="py-0 mb-0 mt-2",
                                        children=[
                                            dbc.Spinner(
                                                color="dark",
                                                show_initially=False,
                                                children=[
                                                    html.Div(
                                                        className="fixed-aspect-ratio",
                                                        children=[
                                                            dcc.Graph(
                                                                id="page-2bis-graph-heatmap-mz-selection",
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
                                                                figure=return_pickled_object(
                                                                    "figures/3D_page",
                                                                    "slices_3D",
                                                                    force_update=False,
                                                                    compute_function=figures.compute_figure_slices_3D,
                                                                ),
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
                    ## Second column
                    dbc.Col(
                        md=6,
                        children=[
                            dbc.Card(
                                style={"maxWidth": "100%", "margin": "0 auto"},
                                children=[
                                    dbc.CardHeader(children="Lipid selection"),
                                    dbc.CardBody(
                                        className="pt-1",
                                        children=[
                                            html.P(
                                                children="Please select the lipids of your choice (up to three):",
                                                className="text-center",
                                            ),
                                            # Dropdown must be wrapped in div, otherwise lazy loading creates bug with tooltips
                                            html.Div(
                                                id="page-2bis-div-dropdown-lipid-names",
                                                children=[
                                                    dcc.Dropdown(
                                                        id="page-2bis-dropdown-lipid-names", options=[], multi=False,
                                                    ),
                                                ],
                                            ),
                                            dbc.Tooltip(
                                                children="Choose the category of your lipid",
                                                target="page-2bis-div-dropdown-lipid-names",
                                                placement="left",
                                            ),
                                            html.Div(
                                                id="page-2bis-div-dropdown-lipid-structures",
                                                children=[
                                                    dcc.Dropdown(
                                                        id="page-2bis-dropdown-lipid-structures",
                                                        options=[],
                                                        multi=False,
                                                        className="mt-2",
                                                    ),
                                                ],
                                            ),
                                            dbc.Tooltip(
                                                children="After choosing the lipid category, choose the structure of your lipid",
                                                target="page-2bis-div-dropdown-lipid-structures",
                                                placement="left",
                                            ),
                                            html.Div(
                                                id="page-2bis-div-dropdown-lipid-cations",
                                                children=[
                                                    dcc.Dropdown(
                                                        id="page-2bis-dropdown-lipid-cations",
                                                        options=[],
                                                        multi=False,
                                                        className="mt-2",
                                                    ),
                                                ],
                                            ),
                                            dbc.Tooltip(
                                                children="After choosing the lipid structure, choose the cation binded to your lipid",
                                                target="page-2bis-div-dropdown-lipid-cations",
                                                placement="left",
                                            ),
                                            # Wrap toasts in div to prevent their expansion
                                            dbc.Toast(
                                                id="page-2bis-toast-lipid-1",
                                                header="name-lipid-1",
                                                icon="danger",
                                                dismissable=True,
                                                is_open=False,
                                                bodyClassName="p-0",
                                                className="mt-3",
                                                style={"margin": "auto"},
                                            ),
                                            dbc.Toast(
                                                id="page-2bis-toast-lipid-2",
                                                header="name-lipid-2",
                                                icon="success",
                                                dismissable=True,
                                                is_open=False,
                                                bodyClassName="p-0",
                                                className="mt-1",
                                                style={"margin": "auto"},
                                            ),
                                            dbc.Toast(
                                                id="page-2bis-toast-lipid-3",
                                                header="name-lipid-3",
                                                icon="primary",
                                                dismissable=True,
                                                is_open=False,
                                                bodyClassName="p-0",
                                                className="mt-1",
                                                style={"margin": "auto"},
                                            ),
                                            html.Div(
                                                id="page-2bis-warning-lipids-number",
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
                                                        id="page-2bis-display-button",
                                                        className="mt-1",
                                                        color="primary",
                                                        disabled=True,
                                                        # block=True,
                                                    ),
                                                ],
                                            ),
                                            # dcc.Download(id="page-2bis-download-data"),
                                        ],
                                    ),
                                ],
                            ),
                            dbc.Card(
                                style={"maxWidth": "100%", "margin": "0 auto"},
                                className="mt-4",
                                children=[
                                    dbc.CardHeader("Range selection"),
                                    dbc.CardBody(
                                        className="pt-1",
                                        children=[
                                            html.Small(
                                                children="Please enter the lower and upper bounds of your m/z range selection. Your selection can't exceed a range of 10m/z, and must be comprised in-between 400 and 1200.",
                                                className="text-center",
                                            ),
                                            dbc.InputGroup(
                                                [
                                                    dbc.Input(
                                                        id="page-2bis-lower-bound",
                                                        placeholder="Lower bound (m/z value)",
                                                    ),
                                                    dbc.Input(
                                                        id="page-2bis-upper-bound",
                                                        placeholder="Upper bound (m/z value)",
                                                    ),
                                                    # dbc.InputGroupAddon(
                                                    dbc.Button(
                                                        "Display",
                                                        id="page-2bis-button-bounds",
                                                        n_clicks=0,
                                                        color="primary",
                                                    ),
                                                    #    addon_type="prepend",
                                                    # ),
                                                ],
                                                size="sm",
                                            ),
                                            html.Small(
                                                children="Or choose a m/z value with a given range. Your selection can't exceed a range of 10m/z, and must be comprised in-between 400 and 1200.",
                                                className="text-center",
                                            ),
                                            dbc.InputGroup(
                                                [
                                                    dbc.Input(id="page-2bis-mz-value", placeholder="m/z value"),
                                                    dbc.Input(id="page-2bis-mz-range", placeholder="Range"),
                                                    # dbc.InputGroupAddon(
                                                    dbc.Button(
                                                        "Display",
                                                        id="page-2bis-button-range",
                                                        n_clicks=0,
                                                        color="primary",
                                                    ),
                                                    #    addon_type="prepend",
                                                    # ),
                                                ],
                                                size="sm",
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                    # Enf of first row
                ],
            ),
        ],
    )

    return page


###### APP CALLBACKS ######

# Function to update the heatmap toast name
@app.app.callback(
    Output("page-2bis-toast-graph-heatmap-mz-selection", "children"), Input("dcc-store-slice-index", "data"),
)
def page_2_update_graph_heatmap_mz_selection(slice_index):
    if slice_index is not None:
        return [
            dbc.Tabs(
                [
                    dbc.Tab(label="TIC per slice in 3D", tab_id="page-2bis-tab-1"),
                    dbc.Tab(label="Lipid selection per slice in 2D", tab_id="page-2bis-tab-2"),
                    dbc.Tab(label="Lipid selection in 3D", tab_id="page-2bis-tab-3"),
                ],
                id="page-2bis-card-tabs",
                active_tab="page-2bis-tab-1",
            ),
        ]

    else:
        return dash.no_update


# Function to plot page-2bis-graph-heatmap-mz-selection when its state get updated
@app.app.callback(
    Output("page-2bis-graph-heatmap-mz-selection", "figure"),
    Input("page-2bis-card-tabs", "active_tab"),
    Input("boundaries-high-resolution-mz-plot", "data"),
    Input("boundaries-low-resolution-mz-plot", "data"),
    Input("page-2bis-selected-lipid-1", "data"),
    Input("page-2bis-selected-lipid-2", "data"),
    Input("page-2bis-selected-lipid-3", "data"),
    Input("page-2bis-button-range", "n_clicks"),
    Input("page-2bis-button-bounds", "n_clicks"),
    Input("page-2bis-display-button", "n_clicks"),
    State("page-2bis-lower-bound", "value"),
    State("page-2bis-upper-bound", "value"),
    State("page-2bis-mz-value", "value"),
    State("page-2bis-mz-range", "value"),
)
def page_2bis_plot_graph_heatmap_mz_selection(
    active_tab,
    bound_high_res,
    bound_low_res,
    l_lipid_1_index,
    l_lipid_2_index,
    l_lipid_3_index,
    n_clicks_button_range,
    n_clicks_button_bounds,
    n_clicks_button_display,
    lb,
    hb,
    mz,
    mz_range,
):

    # Find out which input triggered the function
    id_input = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    # case a mz value and a manual range have been inputed
    if id_input == "page-2bis-button-range":
        mz = float(mz)
        mz_range = float(mz_range)
        if mz > 400 and mz < 1200 and mz_range < 10:
            return dash.no_update
            # return app.slice_store.getSlice(slice_index).return_heatmap(mz - mz_range / 2, mz + mz_range / 2, binary_string=False)
        else:
            return dash.no_update

    # case a two mz bounds values have been inputed
    elif id_input == "page-2bis-button-bounds":
        lb, hb = float(lb), float(hb)
        if lb > 400 and hb < 1200 and hb - lb > 0 and hb - lb < 10:
            return dash.no_update
            # return app.slice_store.getSlice(slice_index).return_heatmap(lb, hb, binary_string=False)
        else:
            return dash.no_update

    # If a lipid selection has been done
    elif id_input == "page-2bis-display-button":

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

            if active_tab == "page-2bis-tab-2":
                return figures.compute_figure_slices_2D(lll_lipid_bounds, normalize_independently=True)
            if active_tab == "page-2bis-tab-3":
                return figures.compute_figure_bubbles_3D(lll_lipid_bounds, normalize_independently=False)

        else:
            # probably the page has just been loaded, so do nothing
            # return app.slice_store.getSlice(slice_index).return_heatmap(binary_string=False)
            return dash.no_update

    return dash.no_update


# Function to refine dropdown names choices
@app.app.callback(
    Output("page-2bis-dropdown-lipid-names", "options"),
    Output("page-2bis-dropdown-lipid-structures", "options"),
    Output("page-2bis-dropdown-lipid-cations", "options"),
    Output("page-2bis-dropdown-lipid-names", "value"),
    Output("page-2bis-dropdown-lipid-structures", "value"),
    Output("page-2bis-dropdown-lipid-cations", "value"),
    Input("page-2bis-dropdown-lipid-names", "value"),
    Input("page-2bis-dropdown-lipid-structures", "value"),
    State("page-2bis-dropdown-lipid-names", "options"),
    State("page-2bis-dropdown-lipid-structures", "options"),
    State("page-2bis-dropdown-lipid-cations", "options"),
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
        if id_input == "page-2bis-dropdown-lipid-names":
            structures = app.data.get_annotations()[app.data.get_annotations()["name"] == name].structure.unique()
            options_structures = [{"label": structure, "value": structure} for structure in sorted(structures)]
            return options_names, options_structures, [], name, None, None

        elif structure is not None:
            if id_input == "page-2bis-dropdown-lipid-structures":
                cations = app.data.get_annotations()[
                    (app.data.get_annotations()["name"] == name)
                    & (app.data.get_annotations()["structure"] == structure)
                ].cation.unique()
                options_cations = [{"label": cation, "value": cation} for cation in sorted(cations)]
                return options_names, options_structures, options_cations, name, structure, None

    return dash.no_update


# Function to add dropdown choice to selection
@app.app.callback(
    Output("page-2bis-toast-lipid-1", "header"),
    Output("page-2bis-toast-lipid-2", "header"),
    Output("page-2bis-toast-lipid-3", "header"),
    Output("page-2bis-selected-lipid-1", "data"),
    Output("page-2bis-selected-lipid-2", "data"),
    Output("page-2bis-selected-lipid-3", "data"),
    Output("page-2bis-toast-lipid-1", "is_open"),
    Output("page-2bis-toast-lipid-2", "is_open"),
    Output("page-2bis-toast-lipid-3", "is_open"),
    Output("page-2bis-last-selected-lipids", "data"),
    Input("page-2bis-dropdown-lipid-cations", "value"),
    Input("page-2bis-toast-lipid-1", "is_open"),
    Input("page-2bis-toast-lipid-2", "is_open"),
    Input("page-2bis-toast-lipid-3", "is_open"),
    State("page-2bis-dropdown-lipid-names", "value"),
    State("page-2bis-dropdown-lipid-structures", "value"),
    State("page-2bis-selected-lipid-1", "data"),
    State("page-2bis-selected-lipid-2", "data"),
    State("page-2bis-selected-lipid-3", "data"),
    State("page-2bis-toast-lipid-1", "header"),
    State("page-2bis-toast-lipid-2", "header"),
    State("page-2bis-toast-lipid-3", "header"),
    State("page-2bis-last-selected-lipids", "data"),
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
    # Take advantage of dash bug that automatically triggers 'page-2bis-dropdown-lipid-cations'
    # everytime the page is loaded, and prevent using dcc-store-slice-index as an input
    # if page-2bis-dropdown-lipid-cations is called while there's no lipid name defined, it means the page just got loaded
    if len(id_input) == 0 or (id_input == "page-2bis-dropdown-lipid-cations" and name is None):
        return "", "", "", empty_lipid_list, empty_lipid_list, empty_lipid_list, False, False, False, []

    # If a lipid has been deleted from a toast
    if value_input == "is_open":

        # Delete corressponding header and index
        if id_input == "page-2bis-toast-lipid-1":
            header_1 = ""
            l_selected_lipids.remove(l_lipid_1_index[0])
            l_lipid_1_index = empty_lipid_list

        elif id_input == "page-2bis-toast-lipid-2":
            header_2 = ""
            l_selected_lipids.remove(l_lipid_2_index[0])
            l_lipid_2_index = empty_lipid_list

        elif id_input == "page-2bis-toast-lipid-3":
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
    elif cation is not None and id_input == "page-2bis-dropdown-lipid-cations":

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
    Output("page-2bis-dropdown-lipid-names", "disabled"),
    Output("page-2bis-dropdown-lipid-structures", "disabled"),
    Output("page-2bis-dropdown-lipid-cations", "disabled"),
    Output("page-2bis-warning-lipids-number", "className"),
    Input("page-2bis-selected-lipid-1", "data"),
    Input("page-2bis-selected-lipid-2", "data"),
    Input("page-2bis-selected-lipid-3", "data"),
)
def page_2bis_disable_dropdowns(l_lipid_1_index, l_lipid_2_index, l_lipid_3_index):

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
    Output("page-2bis-display-button", "disabled"),
    Input("page-2bis-selected-lipid-1", "data"),
    Input("page-2bis-selected-lipid-2", "data"),
    Input("page-2bis-selected-lipid-3", "data"),
)
def tab_2_active_download(l_lipid_1_index, l_lipid_2_index, l_lipid_3_index):
    # If lipids has been selected from the dropdown, activate button
    if np.sum(l_lipid_1_index + l_lipid_2_index + l_lipid_3_index) > -3 * app.data.get_slice_number():
        return False
    else:
        return True


@app.app.callback(
    Output("page-2bis-button-range", "disabled"),
    Input("page-2bis-mz-value", "value"),
    Input("page-2bis-mz-range", "value"),
)
def page_2bis_button_range(mz, mz_range):
    if mz is not None and mz_range is not None:
        mz = float(mz)
        mz_range = float(mz_range)
        if mz > 400 and mz < 1200 and mz_range < 10:
            return False
    return True


@app.app.callback(
    Output("page-2bis-button-bounds", "disabled"),
    Input("page-2bis-lower-bound", "value"),
    Input("page-2bis-upper-bound", "value"),
)
def page_2bis_button_window(lb, hb):
    if lb is not None and hb is not None:
        lb, hb = float(lb), float(hb)
        if lb > 400 and hb < 1200 and hb - lb > 0 and hb - lb < 10:
            return False
    return True

