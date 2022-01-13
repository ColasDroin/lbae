# ! check this
# TO CORRECT: https://dev.to/codemouse92/dead-simple-python-project-structure-and-imports-38c6
import logging
import os
from lbae.modules.tools.misc import logmem

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

# Launch Redis server
os.system("nohup ../redis/redis-6.2.6/src/redis-server &")

# Import the app and define server for gunicorn
logging.info("Starting import chain" + logmem())
from lbae import index

server = index.app.server


# Run the app locally
if __name__ == "__main__":
    logging.info("Starting app" + logmem())
    try:
        index.run()
    except:
        # Shut reddis server
        os.system("../redis/redis-6.2.6/src/redis-cli shutdown")


# To run the app from the server, use the following command in the base lbae folder:
# gunicorn main:server -b:8050 --workers=4
# pkill -P1 gunicorn

# TODO State of the art 3D representation of lipid expression
# TODO debug manual region selection page
# TODO Make lipid expression comparison between 3D structure
# TODO Create a vtk widget to explore 3D lipid data with a transparent continous colormap
# TODO Implement progress bar for slow callbacks with @app.long_callback -> not possible for now as context manager is not supported
# TODO make a careful memory analysis to free more memory
# TODO incoporate new slices
# TODO implement the app as a multipage app when the feature is available on Dash
# TODO have the documentation always open on the right on very big screens to fill empty space
# TODO Implement a "fast mode" with lower resolution images and spectra to have a faster app (for slow connections)
# TODO make layout perfect for every screen size. Maybe automate the process for a given figure shape?
# TODO when everything is stable, create a function that delete all pickle files and repickle everything automatically
# TODO adress all #! comments in the code
# TODO limit Redis entries to e.g. 50
# TODO do quality control, especially when several users are on the app in parallel
# TODO write missing docstrings
# TODO write a brief documentation
# TODO make a docker container for the very final version of the app
