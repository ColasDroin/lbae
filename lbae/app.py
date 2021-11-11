###### IMPORT MODULES ######

# Official modules
import dash
import dash_bootstrap_components as dbc
import pandas as pd
import flask
import numpy as np

# Data module
from tools.SliceData import SliceData
from tools.SliceStore import SliceStore
from tools.SliceAtlas import SliceAtlas

###### APP PRE-COMPUTATIONS ######

# Load data of slice 1 as current slice
initial_slice = 1
slice_store = SliceStore(slice_limit=3, slice_index=initial_slice)
slice_atlas = SliceAtlas(resolution=25)

# pickle all slice files and images
force_pickle = False
if force_pickle:
    SliceStore.pickleAllSlices()
    SliceData.pickle_array_figures()
    slice_atlas.pickle_all_3D_figures(force_recompute=False)
    slice_atlas.pickle_all_masks_and_spectra(force_recompute=True)


# Load lipid annotation (not user-session specific)
df_annotation = pd.read_csv("data/lipid_annotation.csv")
df_annotation["name"] = df_annotation["name"].map(lambda x: x.split("_")[1])

# Load array of figures for the slices
list_array_original_data = SliceData.load_array_figures(load="original_data", atlas_contours=False, atlas_hover=False)
list_array_warped_data = SliceData.load_array_figures(load="warped_data", atlas_contours=False, atlas_hover=False)
list_array_images_atlas = SliceData.load_array_figures(load="atlas", atlas_contours=False, atlas_hover=False)
list_array_projection = SliceData.load_array_figures(load="projection", atlas_contours=False, atlas_hover=False)

list_array_projection_corrected = SliceData.load_array_figures(
    load="projection_corrected", atlas_contours=False, atlas_hover=False
)

list_array_original_data_boundaries = SliceData.load_array_figures(
    load="original_data", atlas_contours=True, atlas_hover=False
)
list_array_warped_data_boundaries = SliceData.load_array_figures(
    load="warped_data", atlas_contours=True, atlas_hover=False
)
list_array_images_atlas_boundaries = SliceData.load_array_figures(load="atlas", atlas_contours=True, atlas_hover=False)
list_array_projection_boundaries = SliceData.load_array_figures(
    load="projection", atlas_contours=True, atlas_hover=False
)
list_array_projection_corrected_boundaries = SliceData.load_array_figures(
    load="projection_corrected", atlas_contours=True, atlas_hover=False
)


list_atlas_boundaries = SliceData.load_array_figures(load="atlas_boundaries", atlas_contours=True, atlas_hover=False)


# Define colors (list and dictionnary)
dic_colors = {"blue": "#50bdda", "green": "#5fa970", "orange": "#de9334", "red": "#df5034", "dark": "#222222"}
l_colors = ["#50bdda", "#5fa970", "#de9334", "#df5034", "#222222"]

# Define basic config for graphs
basic_config = {
    # "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": [
        "select2d",
        "lasso2d",
        "autoScale2d",
        "hoverClosestGl2d",
        "hoverClosestPie",
        "toggleHover",
        "resetViews",
        "toImage: sendDataToCloud",
        "toggleSpikelines",
        "resetViewMapbox",
        "hoverClosestCartesian",
        "hoverCompareCartesian",
    ],
}

###### INSTANTIATE APP ######
server = flask.Flask(__name__)
app = dash.Dash(
    title="Lipids Brain Atlas Explorer",
    external_stylesheets=[dbc.themes.SANDSTONE],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    server=server,
    suppress_callback_exceptions=False,
)

