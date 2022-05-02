###### IMPORT MODULES ######

from dash import html
import dash_mantine_components as dmc
import os
import re
from dash import dcc
import base64

###### DEFFINE PAGE DOCUMENTATION ######

# This function is not optimal but it works and has no requirement for performance
def merge_md(write_doc=False):
    order_final_md = ["_overview", "_data", "_alignment", "_usage", "_about", "_further"]
    final_md = "# Lipid Brain Atlas Explorer documentation \n\n"
    for filename in order_final_md:
        for file in os.listdir(os.path.join(os.getcwd(), "documentation")):
            if file.endswith(".md") and filename in file:
                with open(os.path.join(os.getcwd(), "documentation", file), "r") as f:
                    final_md += f.read() + "\n"
                break
    if write_doc:
        with open(os.path.join(os.getcwd(), "documentation", "documentation.md"), "w") as f:
            f.write(final_md)

    return final_md


def load_md():
    with open(os.path.join(os.getcwd(), "documentation", "documentation.md"), "r") as f:
        md = f.read()
    return md


def convert_md(md, app):
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
