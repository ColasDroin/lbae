###### IMPORT MODULES ######

from dash import html
import dash_mantine_components as dmc
from dash.dependencies import Input, Output, State
from pages.documentation import return_documentation
import app

###### DEFFINE PAGE LAYOUT ######

layout = (
    html.Div(
        id="home-content",
        style={
            "position": "absolute",
            "top": "0px",
            "right": "0px",
            "bottom": "0px",
            "left": "6rem",
            "height": "100vh",
            "background-color": "#1d1c1f",
        },
        children=[
            dmc.Center(
                dmc.Alert(
                    "A connection of at least 10Mbps is recommended to comfortably use the"
                    " application.",
                    title="Information",
                    color="cyan",
                    class_name="my-5 py-5",
                )
            ),
            dmc.Center(
                class_name="w-100",
                children=[
                    # html.H1(
                    #     "Welcome to the Lipid Brain Atlas Explorer",
                    #     className="card-title",
                    # ),
                    dmc.Group(
                        class_name="my-5 py-5",
                        direction="column",
                        align="center",
                        position="center",
                        children=[
                            dmc.Text(
                                "Welcome to the Lipid Brain Atlas Explorer",
                                # size="xl",
                                style={"fontSize": 40, "color": "#dee2e6"},
                                # color="dimmed",
                                align="center",
                            ),
                            html.H1(
                                className="icon-brain my-5 mr-5",
                                style={
                                    "font-size": "12rem",
                                    "color": "#50bdda",
                                    "opacity": "0.9",
                                },
                            ),
                            # Below logo text
                            dmc.Text(
                                "Please start exploring our data by using the navigation bar on the"
                                " right",
                                size="xl",
                                align="center",
                                color="dimmed",
                                class_name="mt-4",
                            ),
                            # Separation and button to documentation
                            # html.Hr(className="my-2"),
                            # html.P(
                            #    className="mb-5",
                            #    children="Press the button below to get to the documentation/paper/etc",
                            # ),
                            dmc.Center(
                                dmc.Button(
                                    "Read documentation",
                                    id="page-0-collapse-doc-button",
                                    class_name="mt-4",
                                    color="cyan",
                                ),
                            ),
                            # Documentation in a bottom drawer
                            dmc.Drawer(
                                children=return_documentation(),
                                id="documentation-offcanvas-home",
                                # title="LBAE documentation",
                                opened=False,
                                padding="md",
                                size="90vh",
                                position="bottom",
                            ),
                            # html.P(
                            #     className="lead d-flex justify-content-center mt-3 mb-5",
                            #     children=[
                            #         dbc.Button(
                            #             "Learn more",
                            #             id="page-0-collapse-doc-button",
                            #             color="primary",
                            #             href="#home-doc",
                            #             external_link=True,
                            #         ),
                            #     ],
                            # ),
                        ],
                    ),
                ],
            ),
        ],
    ),
)


# dbc.Row(
#     justify="center",
#     children=[
#         dbc.Col(
#             md=9,
#             children=[
#                 dbc.Collapse(
#                     children=[
#                         dbc.Card(
#                             className="mt-1 pt-1",
#                             children=[
#                                 dbc.CardHeader("Documentation"),
#                                 dbc.CardBody(
#                                     className="mx-5",
#                                     children=[
#                                         html.H1("Introduction", id="home-doc"),
#                                         html.H2("What is this app about?"),
#                                         html.P("TODO"),
#                                         html.H2("The data"),
#                                         html.P("TODO"),
#                                     ],
#                                 ),
#                             ],
#                         ),
#                     ],
#                     id="page-0-collapse-doc",
#                     is_open=False,
#                 ),
#             ],
#         )
#     ],
# ),


@app.app.callback(
    Output("documentation-offcanvas-home", "opened"),
    [Input("page-0-collapse-doc-button", "n_clicks")],
    [State("documentation-offcanvas-home", "opened")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open
