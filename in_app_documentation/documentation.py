# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

"""This file is used to build the in-app documentation and the readme file."""

# ==================================================================================================
# --- Imports
# ==================================================================================================
import dash_mantine_components as dmc
import os
from dash import dcc

# ==================================================================================================
# --- Functions
# ==================================================================================================
def merge_md(write_doc=False):
    """This function merges the separate files (one per section) from the documentation folder into
    a final markdown document. It is not written in the most optimal way but it works and has no
    requirement for performance.

    Args:
        write_doc (bool, optional): It True, the markdown document is saved as a new file. Defaults
            to False.

    Returns:
        (str): A string representing the documentation of the app written in markdown.
    """
    order_final_md = ["_overview", "_data", "_alignment", "_usage", "_about", "_further"]
    final_md = "# Lipid Brain Atlas Explorer documentation \n\n"
    for filename in order_final_md:
        for file in os.listdir(os.path.join(os.getcwd(), "in_app_documentation")):
            if file.endswith(".md") and filename in file:
                with open(os.path.join(os.getcwd(), "in_app_documentation", file), "r") as f:
                    final_md += f.read() + "\n"
                break
    if write_doc:
        with open(os.path.join(os.getcwd(), "in_app_documentation", "documentation.md"), "w") as f:
            f.write(final_md)

    return final_md


def load_md():
    """This function is used to load the markdown documentation in a string variable from the
    corresponding file.

    Returns:
        (str): A string representing the documentation of the app written in markdown.
    """
    with open(os.path.join(os.getcwd(), "in_app_documentation", "documentation.md"), "r") as f:
        md = f.read()
    return md


def convert_md(md, app):
    """This function is used to convert the markdown documentation in a list of dash components.

    Args:
        md (str): A string representing the documentation of the app written in markdown.
        app (dash.Dash): The dash app, used to fetch the asset folder URL.

    Returns:
        (list): A list of dash components representing the documentation.
    """

    l_md = [x.split(".png)") for y in md.split("\n") for x in y.split("![](")]
    l_md = [x for x in l_md if x != ""]
    for i, md in enumerate(l_md):
        if len(md) > 1:
            md[0] = dmc.Image(
                src=app.get_asset_url(md[0] + ".png"),
                height="400px",
                class_name="mx-auto my-5",
                fit="contain",
            )
            md[1] = dcc.Markdown(md[1])
        else:
            md[0] = dcc.Markdown(md[0])
    l_md = [item for sublist in l_md for item in sublist]

    # Space at the end for clarity
    l_md += [dmc.Space(h=80)]
    return l_md


def return_documentation(app, write_doc=False):
    """This function is used to return the documentation of the app as a dash component.

    Args:
        app (dash.Dash): The dash app, used to fetch the asset folder URL.
        write_doc (bool, optional): It True, the markdown document is saved as a new file. Defaults
            to False.
    Returns:
        (dmc.Center): A Dash Mantine Component representing the documentation in a nice centered and
            scrollable page.
    """
    layout = dmc.Center(
        class_name="mx-auto",
        style={"width": "60%"},
        children=dmc.ScrollArea(
            type="scroll",
            style={"height": "90vh"},
            children=convert_md(merge_md(write_doc), app),
        ),
    )

    return layout
