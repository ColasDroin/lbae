###### IMPORT MODULES ######

# Official modules
import dash
import dash_bootstrap_components as dbc
import pandas as pd
import flask
import numpy as np

# Data module
from lbae.modules.maldi_data import MaldiData
from lbae.modules.figures import Figures

# from tools.SliceAtlas import SliceAtlas

###### APP PRE-COMPUTATIONS ######

# Load data and Figures object
data = MaldiData()
figures = Figures(data)

# Load atlas # ! try to store it as memmap as well?
# slice_atlas = SliceAtlas(resolution=25)

"""
# pickle all slice files and images
force_pickle = False
if force_pickle:
    SliceStore.pickleAllSlices()
    SliceData.pickle_array_figures()
    slice_atlas.pickle_all_3D_figures(force_recompute=False)
    slice_atlas.pickle_all_masks_and_spectra(force_recompute=True)
"""

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


###### INSTANTIATE APP ######
server = flask.Flask(__name__)
app = dash.Dash(
    title="Lipids Brain Atlas Explorer",
    external_stylesheets=[dbc.themes.SANDSTONE],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    server=server,
    suppress_callback_exceptions=False,
)

