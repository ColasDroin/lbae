# Copyright (c) 2022, Colas Droin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

""" This script is used to run the app, setup logging settings, and start redis if needed. 
To run the app with gunicorn, use the following command in the (child) lbae folder: 
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
from modules.tools.misc import logmem  # To track memory usage

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

if app.use_redis:
    os.system("nohup ../redis/redis-6.2.6/src/redis-server ../redis/redis-6.2.6/src/redis.conf &")

# Define app layout
main_content = return_main_content()

# Initialize app with main content
app.layout = main_content

# Give complete layout for callback validation
app.validation_layout = return_validation_layout(main_content)

# Server definition for gunicorn
server = app.server

# ==================================================================================================
# --- App execution
# ==================================================================================================
if __name__ == "__main__":
    logging.info("Starting app" + logmem())
    # try:
    app.run_server(port=8073, debug=True)
    # except:
    #     if app.use_redis:
    #         # Shut reddis server
    #         os.system("../redis/redis-6.2.6/src/redis-cli shutdown")
    #     else:
    #         pass

