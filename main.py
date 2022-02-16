# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This script is used to run the app, setup logging settings, and start redis if needed. 
To run the app with gunicorn, use the following command in the (base) lbae folder: 
gunicorn main:server -b:8050 --workers=2

To kill gunicorn from a linux server (if it doesn't want to die, and respawn automatically), use the
following command: 
pkill -P1 gunicorn
"""

# ==================================================================================================
# --- Imports
# ==================================================================================================

import logging
import os
from lbae.modules.tools.misc import logmem  # To track memory usage

# ==================================================================================================
# --- Logging settings
# ==================================================================================================

# Define logging options for print and debug
logging.basicConfig(
    level=logging.NOTSET,
    format="%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Disable info and debug loggings from external modules
mpl_logger = logging.getLogger("matplotlib")
mpl_logger.setLevel(logging.WARNING)

numexpr_logger = logging.getLogger("numexpr")
numexpr_logger.setLevel(logging.WARNING)

numba_logger = logging.getLogger("numba")
numba_logger.setLevel(logging.WARNING)

# ==================================================================================================
# --- App and server initialization
# ==================================================================================================

logging.info("Starting import chain" + logmem())
from lbae.app import app
from lbae.index import return_main_content, return_validation_layout

use_redis = False
if use_redis:
    os.system("nohup ../redis/redis-6.2.6/src/redis-server ../redis/redis-6.2.6/src/redis.conf &")

# Define app layout
main_content = return_main_content()

# Initialize app with main content
app.layout = main_content

# Give complete layout for callback validation
app.validation_layout = return_validation_layout(main_content)

# Server definition for gunicorn
server = app.server

# Run the app locally
if __name__ == "__main__":
    logging.info("Starting app" + logmem())
    try:
        app.run_server(port=8073, debug=False)
    except:
        if use_redis:
            # Shut reddis server
            os.system("../redis/redis-6.2.6/src/redis-cli shutdown")
        else:
            pass


# TODO make a careful memory analysis to free more memory
# TODO incoporate new brain slices
# TODO adress all # ! and # ? comments in the code
# TODO make the app with tabs instead of pages to accelerate it?
# TODO move layouts to other files
# TODO when everything is stable, create a function that delete all pickle files and repickle everything automatically
# TODO update notebooks with up-to-date classes
# TODO do quality control, especially when several users are on the app in parallel
# TODO correct the name of the files to download
# TODO write missing docstrings
# TODO write documentation
# TODO Make a tour with dash_tour_component?
# TODO Redesign repo according to : https://dev.to/codemouse92/dead-simple-python-project-structure-and-imports-38c6
# TODO make a docker container for the very final version of the app

# ? implement the app as a multipage app when the feature is available on Dash
# ? make layout perfect for every screen size. Maybe automate the process for a given figure shape?
# ? have the documentation always open on the right on very big screens to fill empty space

# http://cajal.epfl.ch:8050/
