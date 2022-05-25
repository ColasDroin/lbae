# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" In this module, the app is instantiated with a given server and cache config. Three global 
variables shared across all user sessions are also instantiated: data, atlas and figures.
"""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard modules
import dash
import dash_bootstrap_components as dbc
from dash.long_callback import DiskcacheLongCallbackManager
import flask
from flask_caching import Cache
import logging
from uuid import uuid4
import diskcache
import os

# LBAE modules
from modules.tools.misc import logmem

logging.info("Memory use before any LBAE import" + logmem())

from modules.maldi_data import MaldiData

logging.info("Memory use after MaldiData import" + logmem())

from modules.figures import Figures

logging.info("Memory use after Figures import" + logmem())

from modules.atlas import Atlas
from modules.launch import Launch
from modules.storage import Storage

# ==================================================================================================
# --- App pre-computations
# ==================================================================================================

logging.info("Memory use before any global variable declaration" + logmem())

# Define if the app will use only a sample of the dataset, and uses a lower resolution for the atlas
SAMPLE_DATA = True

# Define paths for the sample/not sample data
if SAMPLE_DATA:
    path_data = "data_sample/whole_dataset/"
    path_annotations = "data_sample/annotations/"
    path_db = "data_sample/app_data/data.db"
    cache_dir = "data_sample/cache/"
else:
    path_data = "data/whole_dataset/"
    path_annotations = "data/annotations/"
    path_db = "data/app_data/data.db"
    cache_dir = "data/cache/"

# Load shelve database
storage = Storage(path_db)

# Load data
data = MaldiData(path_data, path_annotations, sample_data=SAMPLE_DATA)

# If True, only a small portions of the figures are precomputed (if precomputation has not already
# been done). Used for debugging purposes.
sample = False

# Load Atlas and Figures objects. At first launch, many objects will be precomputed and shelved in
# the classes Atlas and Figures.
atlas = Atlas(data, storage, resolution=25, sample=sample)
figures = Figures(data, storage, atlas, sample=sample)

logging.info("Memory use after three main object have been instantiated" + logmem())


# Compute and shelve potentially missing objects
launch = Launch(data, atlas, figures, storage)
launch.launch()

logging.info("Memory use after main functions have been compiled" + logmem())

# ==================================================================================================
# --- Instantiate app and caching
# ==================================================================================================

# Launch server
server = flask.Flask(__name__)

# Prepare long callback support
launch_uid = uuid4()
cache_long_callback = diskcache.Cache(cache_dir)
long_callback_manager = DiskcacheLongCallbackManager(
    cache_long_callback,
    cache_by=[lambda: launch_uid],
    expire=500,
)

# Instantiate app
app = dash.Dash(
    title="Lipids Brain Atlas Explorer",
    external_stylesheets=[dbc.themes.DARKLY],
    external_scripts=[
        {"src": "https://cdn.jsdelivr.net/npm/dom-to-image@2.6.0/dist/dom-to-image.min.js"}
    ],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    server=server,
    suppress_callback_exceptions=False,
    long_callback_manager=long_callback_manager,
    compress=True,
)


# Add a class attribute to specify if redis is being used
app.use_redis = False

# Set up flask caching in addition to long_callback_manager
if app.use_redis:
    CACHE_CONFIG = {
        # We use 'redis' for faster file retrieval
        "CACHE_TYPE": "redis",
        "CACHE_REDIS_URL": os.environ.get("REDIS_URL", "redis://localhost:6379"),
    }
else:
    CACHE_CONFIG = {
        # We use 'FileSystemCache' as we want the application to be lightweight in term of RAM
        "CACHE_TYPE": "FileSystemCache",
        "CACHE_DIR": cache_dir,
        "CACHE_THRESHOLD": 200,
    }

# Initiate Cache
cache_flask = Cache()
cache_flask.init_app(app.server, config=CACHE_CONFIG)

# Initiate the cache as unlocked
cache_flask.set("locked-cleaning", False)
cache_flask.set("locked-reading", False)
