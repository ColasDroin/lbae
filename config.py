import numpy as np
from matplotlib import cm
from matplotlib.colors import ListedColormap

# ! Clean config

# Define app colors (list and dictionnary)
dic_colors = {
    "blue": "#50bdda",
    "green": "#5fa970",
    "orange": "#de9334",
    "red": "#df5034",
    "dark": "#222222",
}
l_colors = ["#50bdda", "#5fa970", "#de9334", "#df5034", "#222222"]
l_colors_progress = [
    "dark",
    "gray",
    "red",
    "pink",
    "grape",
    "violet",
    "indigo",
    "blue",
    "cyan",
    "teal",
    "green",
    "lime",
    "yellow",
    "orange",
]


# Define basic config for graphs
basic_config = {
    "displayModeBar": False,
    "modeBarButtonsToRemove": [],
    "displaylogo": False,
}


# Colormap with black for 0 values
viridis = cm.get_cmap("viridis", 256)
newcolors = viridis(np.linspace(0, 1, 256))
# black = np.array([30 / 256, 30 / 256, 32 / 256, 1])
black = np.array([0 / 256, 0 / 256, 0 / 256, 1])
newcolors[:1, :] = black
black_viridis = ListedColormap(newcolors)
