# TO CORRECT: https://dev.to/codemouse92/dead-simple-python-project-structure-and-imports-38c6
import logging
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


# Import the app and define server for gunicorn
logging.info("Starting import chain" + logmem())
from lbae import index

server = index.app.server


# Run the app locally
if __name__ == "__main__":
    logging.info("Starting app" + logmem())
    index.run()

# To run the app from the server, use the following command in the base lbae folder:
# gunicorn main:server -b:8050 --workers=1

# TODO debug/accelerate manual region selection page
# TODO accelerate lipid selection per slice in 2D and maybe 3D if possible. Maybe precompute every lipid?
# TODO Make lipid expression comparison between 3D structure
# TODO Implement progress bar for slow callbacks with @app.long_callback -> not possible for now as context manager is not supported
# TODO make a careful memory analysis to free more memory
# TODO incoporate new slices
# TODO implement the app as a multipage app when the feature is available on Dash
# TODO have the documentation always open on the right on very big screens to fill emptyness
# TODO make mask hovering client side in javascript to speed up things a lot. As it is, unusable remotely for now :(
# TODO Implement a "fast mode" with lower resolution images and spectra to have a faster app (for slow connections)
# TODO make layout perfect for every screen size. Maybe automate the process for a given figure shape?
# TODO when everything is stable, create a function that delete all pickle files and repickle everything automatically
# TODO write missing docstrings
# TODO write a brief documentation
