###### IMPORT MODULES ######

import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash import dcc, html
from lbae import app

###### DEFFINE PAGE LAYOUT ######

layout = html.Div(
    id="home-content",
    children=[
        dbc.Row(
            justify="center",
            children=[
                dbc.Col(
                    width="auto",
                    children=[
                        dbc.Card(
                            className="m-5",
                            children=[
                                dbc.CardBody(
                                    children=[
                                        html.H1("Welcome to the Lipid Brain Atlas Explorer", className="card-title"),
                                        html.H1(
                                            className="icon-brain display-1 d-flex justify-content-center my-5 rainbow_text_animated",
                                            style={"font-size": "12rem"},
                                        ),
                                        # Below logo text
                                        html.P(
                                            "Please start exploring our data by using the navigation bar on the right",
                                            className="lead d-flex justify-content-center",
                                        ),
                                        dbc.Alert(
                                            "Warning: a connection of at least 10Mbps is recommended to comfortably use the application.",
                                            color="warning",
                                        ),
                                        # Separation and button to documentation
                                        # html.Hr(className="my-2"),
                                        # html.P(
                                        #    className="mb-5",
                                        #    children="Press the button below to get to the documentation/paper/etc",
                                        # ),
                                        html.P(
                                            className="lead d-flex justify-content-center mt-3 mb-5",
                                            children=[
                                                dbc.Button(
                                                    "Learn more",
                                                    id="page-0-collapse-doc-button",
                                                    color="primary",
                                                    href="#home-doc",
                                                    external_link=True,
                                                ),
                                            ],
                                        ),
                                    ]
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        dbc.Row(
            justify="center",
            children=[
                dbc.Col(
                    md=9,
                    children=[
                        dbc.Collapse(
                            children=[
                                dbc.Card(
                                    className="mt-1 pt-1",
                                    children=[
                                        dbc.CardHeader("Documentation"),
                                        dbc.CardBody(
                                            className="mx-5",
                                            children=[
                                                html.H1("Introduction", id="home-doc"),
                                                html.H2("What is this app about?"),
                                                html.P("TODO"),
                                                html.H2("The data"),
                                                html.P("TODO"),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                            id="page-0-collapse-doc",
                            is_open=False,
                        ),
                    ],
                )
            ],
        ),
    ],
)


@app.app.callback(
    Output("page-0-collapse-doc", "is_open"),
    [Input("page-0-collapse-doc-button", "n_clicks")],
    [State("page-0-collapse-doc", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open
