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
from modules.maldi_data import MaldiData
from modules.figures import Figures
from modules.atlas import Atlas
from modules.tools.misc import logmem

# ==================================================================================================
# --- App pre-computations
# ==================================================================================================

# Load data and Figures object
logging.info("Memory use before any global variable declaration" + logmem())

data = MaldiData()
atlas = Atlas(data, resolution=25)
figures = Figures(data, atlas)

logging.info("Memory use after three main object have been instantiated" + logmem())

# ==================================================================================================
# --- Instantiate app and caching
# ==================================================================================================

# Launch server
server = flask.Flask(__name__)

# Prepare long callback support
launch_uid = uuid4()
cache_long_callback = diskcache.Cache("data/cache/")
long_callback_manager = DiskcacheLongCallbackManager(
    cache_long_callback, cache_by=[lambda: launch_uid], expire=500,
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
        "CACHE_DIR": "data/cache/",
        "CACHE_THRESHOLD": 200,
    }

cache_flask = Cache()
cache_flask.init_app(app.server, config=CACHE_CONFIG)

