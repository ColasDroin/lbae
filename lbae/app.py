###### IMPORT MODULES ######

# Standard imports
import dash
import dash_bootstrap_components as dbc

from dash.long_callback import DiskcacheLongCallbackManager
import flask
from flask_caching import Cache
import logging
from uuid import uuid4
import diskcache

# Homemade modules
from modules.maldi_data import MaldiData
from modules.figures import Figures
from modules.atlas import Atlas
from modules.tools.misc import logmem


###### APP PRE-COMPUTATIONS ######

# Load data and Figures object
logging.info("Memory use before any global variable declaration" + logmem())


data = MaldiData()
atlas = Atlas(data, resolution=25)
figures = Figures(data, atlas)

logging.info("Memory use after three main object have been instantiated" + logmem())

###### INSTANTIATE APP ######
server = flask.Flask(__name__)

# For long callback support
launch_uid = uuid4()
cache_long_callback = diskcache.Cache("data/temp/")
long_callback_manager = DiskcacheLongCallbackManager(
    cache_long_callback, cache_by=[lambda: launch_uid], expire=500,
)

# Instantiate app
app = dash.Dash(
    title="Lipids Brain Atlas Explorer",
    external_stylesheets=[dbc.themes.SANDSTONE],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    server=server,
    suppress_callback_exceptions=False,
    long_callback_manager=long_callback_manager,
    compress=True,
)

CACHE_CONFIG = {
    # We use 'FileSystemCache' as we want to keep the application very lightweight in term of RAM memory
    "CACHE_TYPE": "FileSystemCache",
    "CACHE_DIR": "data/temp/",
    # "CACHE_TYPE": "redis",
    # "CACHE_REDIS_URL": os.environ.get("REDIS_URL", "redis://localhost:6379"),
    "CACHE_THRESHOLD": 200,
}
cache_flask = Cache()
cache_flask.init_app(app.server, config=CACHE_CONFIG)

