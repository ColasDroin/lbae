###### IMPORT MODULES ######

from dash import html
import dash_mantine_components as dmc

###### DEFFINE PAGE DOCUMENTATION ######


def return_documentation():
    layout = html.Div(
        children=[
            html.H1(children="LBAE Documentation"),
            dmc.Text(
                "Please start exploring our data by using the navigation bar on the right",
                size="xl",
                align="center",
                color="dimmed",
                class_name="mt-4",
            ),
            html.Hr(className="my-2"),
            html.P(
                className="mb-5",
                children="Press the button below to get to the documentation/paper/etc",
            ),
        ],
    )

    return layout

