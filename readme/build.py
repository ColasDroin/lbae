# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

"""This file is used to build the readme file."""

# ==================================================================================================
# --- Imports
# ==================================================================================================
import os

# Move to root directory for easier path handling
os.chdir("..")

# ==================================================================================================
# --- Functions
# ==================================================================================================
def write_readme():
    """This function merges the separate files (one per section) from the documentation and readme
    folders into a final markdown document, saved as README.md.
    """
    order_final_md = [
        "_overview",
        "_data",
        "_alignment",
        "_usage_readme",
        "_about",
        "_further_readme",
    ]
    final_md = "# Lipid Brain Atlas Explorer documentation \n\n"
    final_md += """<p align="center"><img src="readme/brain.gif" alt="animated" /></p>"""
    final_md += "\n\n"
    for filename in order_final_md:
        for file in list(os.listdir(os.path.join(os.getcwd(), "documentation"))) + list(
            os.listdir(os.path.join(os.getcwd(), "readme"))
        ):
            if file.endswith("_readme.md") and filename in file:
                with open(os.path.join(os.getcwd(), "readme", file), "r") as f:
                    final_md += f.read() + "\n"
                break
            elif file.endswith(".md") and filename in file:
                with open(os.path.join(os.getcwd(), "documentation", file), "r") as f:
                    current_paragraph = f.read()
                    if "ressources" in current_paragraph:
                        current_paragraph = current_paragraph.replace(
                            "ressources/", "assets/ressources/"
                        )
                    final_md += current_paragraph + "\n"
                break

    with open(os.path.join(os.getcwd(), "README.md"), "w") as f:
        f.write(final_md)


write_readme()
