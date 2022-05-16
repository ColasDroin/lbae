# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This file contains some variables used for styling/configuring Plotly widgets."""

# ==================================================================================================
# --- Imports
# ==================================================================================================
import numpy as np
from matplotlib import cm
from matplotlib.colors import ListedColormap

# ==================================================================================================
# --- Style and configuration
# ==================================================================================================

# Define app colors (list and dictionnary)
dic_colors = {
    "blue": "#50bdda",
    "green": "#5fa970",
    "orange": "#de9334",
    "red": "#df5034",
    "dark": "#222222",
}
l_colors = ["#50bdda", "#5fa970", "#de9334", "#df5034", "#222222"]


# Define basic config for graphs
basic_config = {
    "displayModeBar": False,
    "modeBarButtonsToRemove": [],
    "displaylogo": False,
}

# Viridis colormap with black for 0 values
newcolors = cm.get_cmap("viridis", 256)(np.linspace(0, 1, 256))
newcolors[:1, :] = np.array([0 / 256, 0 / 256, 0 / 256, 1])
black_viridis = ListedColormap(newcolors)
