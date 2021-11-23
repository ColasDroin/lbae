###### IMPORT MODULES ######

# Official modules
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
import uuid
import dash
import time
import dash_loading_spinners as dls
import orjson

# App modules
from app import app, initial_slice, slice_atlas
from pages import (
    sidebar,
    home,
    load_slice,
    lipid_selection,
    lipid_selection_all_slices,
    region_analysis,
    threeD_exploration,
)

###### DEFINE APP LAYOUT ######

# Define server for gunicorn
server = app.server

# Define basic config for graphs
basic_config = {
    "displayModeBar": False,
    "modeBarButtonsToRemove": [],
    "displaylogo": False,
}

# list of empty lipid indexes for the dropdown of page 2bis
empty_lipid_list = [-1 for i in range(slice_atlas.n_slices)]

# Responsive layout
def return_main_content():

    # Record session id in case sessions need to be individualized (i.e. we handle better global variables)
    session_id = str(uuid.uuid4())

    # Define static content
    main_content = html.Div(
        children=[
            # To handle url since multi-page app
            dcc.Location(id="url", refresh=False),
            # Record session id, useful to trigger callbacks at initialization
            dcc.Store(id="session-id", data=session_id),
            # Record slice index, to keep track of current slice
            dcc.Store(id="dcc-store-slice-index", data=initial_slice),
            # Record the state of the range sliders for low and high resolution spectra in page 2
            dcc.Store(id="boundaries-low-resolution-mz-plot"),
            dcc.Store(id="boundaries-high-resolution-mz-plot"),
            # Record the lipids selected in page 2 (made with a dropdown for now)
            dcc.Store(id="page-2-selected-lipid-1", data=-1),
            dcc.Store(id="page-2-selected-lipid-2", data=-1),
            dcc.Store(id="page-2-selected-lipid-3", data=-1),
            dcc.Store(id="page-2-last-selected-lipids", data=[]),
            # Record the lipids selected in page 2bis
            dcc.Store(id="page-2bis-selected-lipid-1", data=empty_lipid_list),
            dcc.Store(id="page-2bis-selected-lipid-2", data=empty_lipid_list),
            dcc.Store(id="page-2bis-selected-lipid-3", data=empty_lipid_list),
            dcc.Store(id="page-2bis-last-selected-lipids", data=[]),
            # Record the shapes drawn in page 3
            dcc.Store(id="dcc-store-color-mask", data=[]),
            dcc.Store(id="dcc-store-reset", data=False),
            dcc.Store(id="dcc-store-shapes-and-masks", data=[]),
            dcc.Store(id="dcc-store-list-idx-lipids", data=[]),
            # Record the annotated paths drawn in page 3
            dcc.Store(id="page-3-dcc-store-path-heatmap"),
            # Record the computed spectra drawn in page 3
            dcc.Store(id="dcc-store-list-mz-spectra", data=[]),
            # Record the lipids expressed in the region in page 3
            dcc.Store(id="page-3-dcc-store-lipids-region", data=[]),
            # List of stores to compute loading bar
            dcc.Store(id="page-3-dcc-store-loading-1", data=False),
            dcc.Store(id="page-3-dcc-store-loading-2", data=False),
            dcc.Store(id="page-3-dcc-store-loading-3", data=False),
            dcc.Store(id="page-3-dcc-store-loading-4", data=False),
            dcc.Store(id="page-3-dcc-store-loading-5", data=False),
            # Actual app layout
            dbc.Container(
                fluid=True,
                children=[
                    sidebar.layout,
                    html.Div(id="content"),
                    # dbc.Spinner(
                    dls.Tunnel(
                        id="main-spinner",
                        children=html.Div(id="empty-content"),
                        fullscreen=True,
                        fullscreen_style={"margin-left": "6rem", "padding-right": "7rem",},
                        debounce=200,
                        # type="grow",
                        width=100,
                    ),
                ],
            ),
        ],
    )
    return main_content


main_content = return_main_content()

# Initialize app with main content
app.layout = main_content

# Give complete layout for callback validation
app.validation_layout = html.Div(
    [
        main_content,
        home.layout,
        load_slice.return_layout(initial_slice=initial_slice),
        lipid_selection.return_layout(),
        lipid_selection_all_slices.return_layout(),
        region_analysis.return_layout(),
        threeD_exploration.return_layout(),
    ]
)


###### APP CALLBACK FOR URL ######


@app.callback(
    Output("content", "children"),
    Output("empty-content", "children"),
    Input("url", "pathname"),
    State("dcc-store-slice-index", "data"),
)
def render_page_content(pathname, slice_index):
    # Set the content according to the current pathname
    if pathname == "/":
        page = home.layout

    elif pathname == "/load-slice":
        page = (load_slice.return_layout(initial_slice=slice_index),)

    elif pathname == "/lipid-selection":
        page = (lipid_selection.return_layout(slice_index=slice_index),)

    elif pathname == "/lipid-selection-all-slices":
        page = (lipid_selection_all_slices.return_layout(),)

    elif pathname == "/region-analysis":
        page = (region_analysis.return_layout(slice_index=slice_index),)

    elif pathname == "/3D-exploration":
        page = (threeD_exploration.return_layout(),)

    else:
        # If the user tries to reach a different page, return a 404 message
        page = dbc.Jumbotron(
            children=[
                html.H1("404: Not found", className="text-danger"),
                html.Hr(),
                html.P(f"The pathname {pathname} was not recognised..."),
            ]
        )
    return page, ""


# Run app from local console (not gunicorn)
if __name__ == "__main__":
    app.run_server(port=8060, debug=False)

# pkill -P1 gunicorn
