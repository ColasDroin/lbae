###### IMPORT MODULES ######

from dash import html
import dash_mantine_components as dmc
import os
import re

###### DEFFINE PAGE DOCUMENTATION ######

# This function is not optimal but it works and has no requirement for performance
def merge_md():
    order_final_md = ["_overview", "_data", "_alignment", "_usage", "_about", "_further"]
    final_md = "# Lipid Brain Atlas Explorer documentation \n\n"
    for filename in order_final_md:
        for file in os.listdir(os.path.join(os.getcwd(), ".")):
            if file.endswith(".md") and filename in file:
                with open(os.path.join(os.getcwd(), ".", file), "r") as f:
                    final_md += f.read() + "\n"
                break

    with open(os.path.join(os.getcwd(), ".", "documentation.md"), "w") as f:
        f.write(final_md)

    return final_md


def return_documentation():
    layout = dmc.Center(
        class_name="mx-auto",
        style={"width": "60%"},
        children=dmc.ScrollArea(
            type="scroll",
            style={"height": "90vh"},
            children=[
                dmc.Text(
                    "Lipid Brain Atlas Explorer Documentation",
                    style={"fontSize": 40, "color": "#1fafc8"},
                    align="center",
                ),
                dmc.Title(
                    "Overview",
                    order=2,
                    align="left",
                    class_name="mt-5",
                    style={"color": "white"},
                ),
                dmc.Text(
                    children=[
                        html.Span(
                            "The Lipid Brain Atlas Explorer is a web-application developped as part"
                            " of the"
                        ),
                        html.Em(" Lipid Brain Atlas project"),
                        html.Span(", led by the "),
                        html.A(
                            "Lipid Cell Biology lab (EPFL)",
                            href="https://www.epfl.ch/labs/dangelo-lab/",
                        ),
                        html.Span(" and the "),
                        html.A(
                            "Neurodevelopmental Systems Biology (EPFL)",
                            href="https://www.epfl.ch/labs/nsbl/",
                        ),
                        html.Span(
                            ". It is thought as a graphical user interface"
                            " to assist the inspection and the analysis of a large"
                            " mass-spectrometry dataset of lipids distribution at micrometric"
                            " resolution across the entire mouse brain. All of the brain slices"
                            " aquired have prealably been registered to the Mouse Brain Common"
                            " Coordinate Framework v3.0 (CCFv3), allowing for a hierarchically"
                            " structured annotation of our data. This registration can be used to"
                            " perform analyses comparing neuroanatomical regions, e.g. averaging"
                            " and comparing lipid abundance in each region and make an enrichment"
                            " analysis ("
                        ),
                        html.Em("region analysis"),
                        html.Span(
                            " page, in the app). It was also used to"
                            " combine the 2D slice acquisitions into a browsable 3d model ("
                        ),
                        html.Em("three dimensional analysis "),
                        html.Span("page, in the app)."),
                    ],
                    class_name="mt-4 text-justify",
                    size="xl",
                ),
                dmc.Text(
                    children=(
                        "We hope that this application will be of great help to query the Lipid"
                        " Brain Atlas to guide your hypotheses and experiments, and more generally"
                        " to achieve a better understanding of the cellular mechanisms involving"
                        " lipids that are fundamental for nervous system development and function."
                    ),
                    size="xl",
                ),
                dmc.Text(
                    children=(
                        "We hope that this application will be of great help to query the Lipid"
                        " Brain Atlas to guide your hypotheses and experiments, and more generally"
                        " to achieve a better understanding of the cellular mechanisms involving"
                        " lipids that are fundamental for nervous system development and function."
                    ),
                    size="xl",
                ),
                dmc.Title(
                    "Data",
                    order=2,
                    align="left",
                    class_name="mt-5",
                    style={"color": "white"},
                ),
                dmc.Text(
                    children=(
                        " The multidimensional atlas of the mouse brain lipidome that you can"
                        " explore through LBAE has been entirely acquired from MALDI Mass"
                        " Spectrometry Imaging (MALDI-MSI) experiments."
                    ),
                    class_name="mt-4",
                    size="xl",
                ),
                dmc.Title(
                    "Alignment to the Allen Brain Atlas",
                    order=2,
                    align="left",
                    class_name="mt-5",
                    style={"color": "white"},
                ),
                dmc.Text(
                    children="TODO",
                    size="xl",
                    class_name="mt-4",
                ),
                dmc.Title(
                    "How to use the app",
                    order=2,
                    align="left",
                    class_name="mt-5",
                    style={"color": "white"},
                ),
                dmc.Text(
                    children="TODO",
                    size="xl",
                    class_name="mt-4",
                ),
                dmc.Title(
                    "Lipid selection page",
                    order=3,
                    align="left",
                    class_name="mt-5",
                    style={"color": "white"},
                ),
                dmc.Text(
                    children="TODO",
                    size="lg",
                    class_name="mt-4 pl-2",
                ),
            ],
        ),
    )

    return layout


if __name__ == "__main__":
    print(merge_md())
