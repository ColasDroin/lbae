###### IMPORT MODULES ######

from typing import Container
import dash_bootstrap_components as dbc
from dash import dcc, html

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
        dbc.Nav(
            vertical=True,
            pills=True,
            children=[
                # Link to page 1
                dbc.NavLink(
                    id="sidebar-page-1",
                    href="/load-slice",
                    active="exact",
                    children=[html.I(className="icon-upload fs-4", style={"margin-left": "0.2em"})],
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
                        html.I(className="icon-chart-bar fs-4", style={"margin-left": "0.2em"})
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
                    children=[html.I(className="icon-3d fs-4", style={"margin-left": "0.2em"})],
                    className="my-4",
                ),
                dbc.Tooltip(
                    children="Analyse brain data in 3D", target="sidebar-page-4", placement="right"
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
                html.H4(
                    id="sidebar-copyright", className="sidebar-copyright icon-cc ml-1 mb-3 fs-1"
                ),
                dbc.Tooltip(
                    children="Copyright EPFL 2022", target="sidebar-copyright", placement="right"
                ),
            ],
        ),
    ],
)

