###### IMPORT MODULES ######

from dash import html
import dash_mantine_components as dmc

###### DEFFINE PAGE DOCUMENTATION ######


def return_documentation():
    layout = dmc.Center(
        class_name="w-75 ml-auto mr-auto",
        children=html.Div(
            children=[
                dmc.Title("Lipid Brain Atlas Explorer Documentation", order=1, align="center"),
                dmc.Title("Overview", order=2, align="left", class_name="mt-5"),
                dmc.Text(
                    children="The Lipid Brain Atlas Explorer is a web-application developped as part of the "
                    + "Lipid Brain Atlas project, led by the Lipid Cell Biology lab (EPFL) and the "
                    + "Neurodevelopmental Systems Biology (EPFL). It is thought as a graphical user"
                    + " interface to assist the inspection and the analysis of a multidimensional "
                    + "atlas of the brain lipidome.",
                    class_name="mt-4",
                ),
            ],
        ),
    )

    return layout

