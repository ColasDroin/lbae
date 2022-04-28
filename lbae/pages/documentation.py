###### IMPORT MODULES ######

from dash import html
import dash_mantine_components as dmc

###### DEFFINE PAGE DOCUMENTATION ######


def return_documentation():
    layout = dmc.Center(
        class_name="mx-auto",
        style={"width": "60%"},
        children=html.Div(
            children=[
                dmc.Title("Lipid Brain Atlas Explorer Documentation", order=1, align="center"),
                dmc.Title("Overview", order=2, align="left", class_name="mt-5"),
                dmc.Text(
                    children=(
                        "The Lipid Brain Atlas Explorer is a web-application developped as part of"
                        " Lipid Brain Atlas project, led by the Lipid Cell Biology lab (EPFL) and"
                        " the Neurodevelopmental Systems Biology (EPFL). It is thought as a"
                        " graphical user interface to assist the inspection and the analysis of a a"
                        " large mass-spectrometry dataset of lipids distribution at micrometric"
                        " resolution across the entire mouse brain."
                    ),
                    class_name="mt-4",
                    size="lg",
                ),
                dmc.Text(
                    children=(
                        "We hope that this application will be of great help to query the Lipid"
                        " Brain Atlas to guide your hypotheses and experiments, to achieve a better"
                        " understanding of the cellular mechanisms involving lipids that are"
                        " fundamental for nervous system development and function."
                    ),
                    size="lg",
                ),
                dmc.Title("Data", order=2, align="left", class_name="mt-5"),
                dmc.Text(
                    children=(
                        " The multidimensional atlas of the mouse brain lipidome that you can"
                        " explore through LBAE has been entirely acquired from MALDI Mass"
                        " Spectrometry Imaging (MALDI-MSI) experiments."
                    ),
                    class_name="mt-4",
                    size="lg",
                ),
                dmc.Title(
                    "Alignment to the Allen Brain Atlas", order=2, align="left", class_name="mt-5"
                ),
                dmc.Text(
                    children="TODO",
                    size="lg",
                    class_name="mt-4",
                ),
                dmc.Title("How to use the app", order=2, align="left", class_name="mt-5"),
                dmc.Text(
                    children="TODO",
                    size="lg",
                    class_name="mt-4",
                ),
                dmc.Title("Lipid selection page", order=3, align="left", class_name="mt-5"),
                dmc.Text(
                    children="TODO",
                    size="md",
                    class_name="mt-4 pl-2",
                ),
            ],
        ),
    )

    return layout
