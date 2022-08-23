# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This script is used to run the app and setup logging settings. 
To run the app with gunicorn, use the following command in the main lbae folder: 
gunicorn main:server -b:8050 --worker-class gevent --threads 4 --workers=1
Or, to run the app ignoring hangup signals, i.e. not stopping when disconnecting from the server:
nohup gunicorn main:server -b:8050 --worker-class gevent --threads 4 --workers=1 &
The app will then run on http://cajal.epfl.ch:8050/

To kill gunicorn from a linux server (if it doesn't want to die, and respawn automatically), use the
following command: 
pkill -P1 gunicorn

For a faster app, please install orjson with pip before launching the app:
pip install orjson
"""

# ==================================================================================================
# --- Imports
# ==================================================================================================

import logging
from modules.tools.misc import logmem  # To track memory usage
import dash_mantine_components as dmc

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
from app import app
from index import return_main_content, return_validation_layout

# Define app layout
main_content = return_main_content()

# Initialize app with main content and dark theme
app.layout = dmc.MantineProvider(
    theme={"colorScheme": "dark"},
    children=[
        main_content,
    ],
)

# Give complete layout for callback validation
app.validation_layout = return_validation_layout(main_content)

# Server definition for gunicorn
server = app.server

# ==================================================================================================
# --- App execution
# ==================================================================================================
if __name__ == "__main__":
    logging.info("Starting app" + logmem())
    try:
        app.run(port=8077, debug=False)
    except Exception as e:
        print(e)
