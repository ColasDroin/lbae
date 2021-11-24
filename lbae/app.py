###### IMPORT MODULES ######

# Standard imports
import dash
import dash_bootstrap_components as dbc
import flask

# Homemade modules
from lbae.modules.maldi_data import MaldiData
from lbae.modules.figures import Figures
from lbae.modules.atlas import Atlas
from lbae.modules.tools.misc import return_pickled_object

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
list_array_original_data = figures.compute_array_figures_basic_image(
    load="original_data", atlas_contours=False, atlas_hover=False
)
list_array_warped_data = figures.compute_array_figures_basic_image(
    load="warped_data", atlas_contours=False, atlas_hover=False
)
list_array_images_atlas = figures.compute_array_figures_basic_image(
    load="atlas", atlas_contours=False, atlas_hover=False
)
list_array_projection_corrected = figures.compute_array_figures_basic_image(
    load="projection_corrected", atlas_contours=False, atlas_hover=False
)
list_array_original_data_boundaries = figures.compute_array_figures_basic_image(
    load="original_data", atlas_contours=True, atlas_hover=False
)
list_array_warped_data_boundaries = figures.compute_array_figures_basic_image(
    load="warped_data", atlas_contours=True, atlas_hover=False
)
list_array_images_atlas_boundaries = figures.compute_array_figures_basic_image(
    load="atlas", atlas_contours=True, atlas_hover=False
)
list_array_projection_corrected_boundaries = figures.compute_array_figures_basic_image(
    load="projection_corrected", atlas_contours=True, atlas_hover=False
)
list_atlas_boundaries = figures.compute_array_figures_basic_image(
    load="atlas_boundaries", atlas_contours=True, atlas_hover=False
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

