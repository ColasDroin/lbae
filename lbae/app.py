###### IMPORT MODULES ######

# Standard imports
import dash
import dash_bootstrap_components as dbc
import flask
import numpy as np
import logging

# Homemade modules
from lbae.modules.maldi_data import MaldiData
from lbae.modules.figures import Figures
from lbae.modules.atlas import Atlas
from lbae.modules.tools.misc import return_pickled_object
from lbae.modules.tools.memuse import logmem


###### APP PRE-COMPUTATIONS ######

# Load data and Figures object


data = MaldiData()
atlas = Atlas(resolution=25)
figures = Figures(data, atlas)

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
list_array_original_data = return_pickled_object(
    "figures/load_page",
    "array_figures_basic_image",
    force_update=False,
    compute_function=figures.compute_array_figures_basic_image,
    type_figure="original_data",
    plot_atlas_contours=False,
)
list_array_warped_data = return_pickled_object(
    "figures/load_page",
    "array_figures_basic_image",
    force_update=False,
    compute_function=figures.compute_array_figures_basic_image,
    type_figure="warped_data",
    plot_atlas_contours=False,
)

list_array_images_atlas = return_pickled_object(
    "figures/load_page",
    "array_figures_basic_image",
    force_update=False,
    compute_function=figures.compute_array_figures_basic_image,
    type_figure="atlas",
    plot_atlas_contours=False,
)

list_array_projection_corrected = return_pickled_object(
    "figures/load_page",
    "array_figures_basic_image",
    force_update=False,
    compute_function=figures.compute_array_figures_basic_image,
    type_figure="projection_corrected",
    plot_atlas_contours=False,
)

list_array_original_data_boundaries = return_pickled_object(
    "figures/load_page",
    "array_figures_basic_image",
    force_update=False,
    compute_function=figures.compute_array_figures_basic_image,
    type_figure="original_data",
    plot_atlas_contours=True,
)


list_array_warped_data_boundaries = return_pickled_object(
    "figures/load_page",
    "array_figures_basic_image",
    force_update=False,
    compute_function=figures.compute_array_figures_basic_image,
    type_figure="warped_data",
    plot_atlas_contours=True,
)

# ! Computing this takes a lot of time
list_array_images_atlas_boundaries = return_pickled_object(
    "figures/load_page",
    "array_figures_basic_image",
    force_update=False,
    compute_function=figures.compute_array_figures_basic_image,
    type_figure="atlas",
    plot_atlas_contours=True,
)

list_array_projection_corrected_boundaries = return_pickled_object(
    "figures/load_page",
    "array_figures_basic_image",
    force_update=False,
    compute_function=figures.compute_array_figures_basic_image,
    type_figure="projection_corrected",
    plot_atlas_contours=True,
)

list_array_atlas_boundaries = return_pickled_object(
    "figures/load_page",
    "array_figures_basic_image",
    force_update=False,
    compute_function=figures.compute_array_figures_basic_image,
    type_figure="atlas_boundaries",
    plot_atlas_contours=True,
)


###### INSTANTIATE APP ######
server = flask.Flask(__name__)
app = dash.Dash(
    title="Lipids Brain Atlas Explorer",
    external_stylesheets=[dbc.themes.SANDSTONE],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    server=server,
    suppress_callback_exceptions=False,
)

