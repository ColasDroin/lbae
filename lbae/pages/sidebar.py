###### IMPORT MODULES ######

# Standard modules
import dash_bootstrap_components as dbc
from dash import html
import dash_mantine_components as dmc
from dash.dependencies import Input, Output, State

# LBAE modules
import app
from pages.documentation import return_documentation

###### DEFFINE PAGE LAYOUT ######

layout = html.Div(
    className="sidebar",
    children=[
        # Header with logo
        dbc.Nav(
            id="sidebar-title",
            className="sidebar-header",
            vertical=True,
            pills=True,
            children=[
                dbc.NavLink(
                    href="/",
                    active="exact",
                    className="d-flex justify-content-center align-items-center",
                    children=[
                        html.I(className="icon-brain fs-2 m-auto"),
                        # html.H5(children="Lipid Brain Explorer", className="ml-3 mb-2"),
                    ],
                ),
            ],
        ),
        dbc.Tooltip(
            children="Return to homepage and documentation.",
            target="sidebar-title",
            placement="right",
        ),
        html.Hr(),
        # Navebar to different pages
        dmc.Center(
            style={"height": "60%"},
            children=[
                dbc.Nav(
                    vertical=True,
                    pills=True,
                    children=[
                        # Link to page 1
                        dbc.NavLink(
                            id="sidebar-page-1",
                            href="/load-slice",
                            active="exact",
                            children=[
                                html.I(className="icon-upload fs-4", style={"margin-left": "0.2em"})
                            ],
                            className="mt-3 mb-2",
                        ),
                        dbc.Tooltip(
                            # container="content",
                            children="Choose the slice you want to discover",
                            target="sidebar-page-1",
                            placement="right",
                        ),
                        # Link to page 2
                        dbc.NavLink(
                            id="sidebar-page-2",
                            href="/lipid-selection",
                            active="exact",
                            children=[
                                html.I(className="icon-lipid fs-4", style={"margin-left": "0.2em"})
                            ],  # html.Span("Per-lipid analysis"),],
                            className="my-4",
                        ),
                        dbc.Tooltip(
                            children="Analyse spectrum and brain composition by custom lipid selection",
                            target="sidebar-page-2",
                            placement="right",
                        ),
                        # Link to page 3
                        dbc.NavLink(
                            id="sidebar-page-3",
                            href="/region-analysis",
                            active="exact",
                            children=[
                                html.I(
                                    className="icon-chart-bar fs-4", style={"margin-left": "0.2em"}
                                )
                            ],  # html.Span("Per-region analysis"),],
                            className="my-4",
                        ),
                        dbc.Tooltip(
                            children="Analyse lipid composition by brain region",
                            target="sidebar-page-3",
                            placement="right",
                        ),
                        # Link to page 4
                        dbc.NavLink(
                            id="sidebar-page-4",
                            href="/3D-exploration",
                            active="exact",
                            # disabled=True,
                            children=[
                                html.I(className="icon-3d fs-4", style={"margin-left": "0.2em"})
                            ],
                            className="my-4",
                        ),
                        dbc.Tooltip(
                            children="Analyse brain data in 3D",
                            target="sidebar-page-4",
                            placement="right",
                        ),
                        # # Link to page 5
                        # dbc.NavLink(
                        #     id="sidebar-page-5",
                        #     href="/atlas-exploration",
                        #     active="exact",
                        #     children=[html.I(className="icon-library pl-1")],
                        # ),
                        # dbc.Tooltip(children="Explore Allen brain atlas data", target="sidebar-page-5", placement="right",),
                        # Copyright
                        # Link to page 4
                        html.Div(
                            className="sidebar-bottom",
                            children=[
                                dbc.NavLink(
                                    id="sidebar-documentation",
                                    n_clicks=0,
                                    active="exact",
                                    children=[html.I(className="icon-library mb-5 fs-2",)],
                                ),
                                dbc.Tooltip(
                                    children="Open documentation",
                                    target="sidebar-documentation",
                                    placement="right",
                                ),
                                dmc.Drawer(
                                    children=return_documentation(),
                                    id="documentation-offcanvas",
                                    title="LBAE documentation",
                                    opened=False,
                                    padding="md",
                                    size="80%",
                                    position="bottom",
                                ),
                                html.H4(
                                    id="sidebar-copyright",
                                    className="icon-cc mb-3 mt-5 fs-1",
                                    style={"color": "#dee2e6"},
                                ),
                                dbc.Tooltip(
                                    children="Copyright EPFL 2022",
                                    target="sidebar-copyright",
                                    placement="right",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)

# Callback for documentation
@app.app.callback(
    Output("documentation-offcanvas", "opened"),
    [Input("sidebar-documentation", "n_clicks")],
    [State("documentation-offcanvas", "opened")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open
