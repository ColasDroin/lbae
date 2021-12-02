###### IMPORT MODULES ######

# Official modules
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
import uuid
import dash_loading_spinners as dls
import logging

# Homemade modules
from lbae.app import app, data
from lbae.pages import (
    sidebar,
    home,
    load_slice,
    lipid_selection,
    lipid_selection_all_slices,
    region_analysis,
    # threeD_exploration,
)
from lbae.config import basic_config
from lbae.modules.tools.memuse import logmem

###### DEFINE APP LAYOUT ######


# Responsive layout
def return_main_content():

    # list of empty lipid indexes for the dropdown of page 2bis
    empty_lipid_list = [-1 for i in range(data.get_slice_number())]

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
            dcc.Store(id="dcc-store-slice-index", data=1),
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
                    dls.Tunnel(
                        id="main-spinner",
                        children=html.Div(id="empty-content"),
                        fullscreen=True,
                        fullscreen_style={"margin-left": "6rem", "padding-right": "7rem",},
                        debounce=200,
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
        load_slice.return_layout(basic_config=basic_config),
        lipid_selection.return_layout(basic_config=basic_config),
        lipid_selection_all_slices.return_layout(basic_config=basic_config),
        region_analysis.return_layout(basic_config=basic_config),
        # threeD_exploration.return_layout(),
    ]
)


###### APP CALLBACK FOR URL ######


@app.callback(Output("content", "children"), Output("empty-content", "children"), Input("url", "pathname"))
def render_page_content(pathname):
    logging.info("Page" + pathname + "has been selected" + logmem())

    # Set the content according to the current pathname
    if pathname == "/":
        page = home.layout

    elif pathname == "/load-slice":
        page = load_slice.return_layout(basic_config=basic_config)

    elif pathname == "/lipid-selection":
        page = lipid_selection.return_layout(basic_config=basic_config)

    elif pathname == "/lipid-selection-all-slices":
        page = lipid_selection_all_slices.return_layout(basic_config=basic_config)

    elif pathname == "/region-analysis":
        page = region_analysis.return_layout(basic_config=basic_config)

    # elif pathname == "/3D-exploration":
    #    page = threeD_exploration.return_layout()

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


def run():
    app.run_server(port=8060, debug=False)


# Run app from local console (not gunicorn)
# if __name__ == "__main__":
#    app.run_server(port=8060, debug=False)

# pkill -P1 gunicorn
