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
# TODO Finish layout where it needs to be finished (especially region analysis, where it was only done for XXL size)
# TODO make manual region selection page responsive
# TODO Make lipid expression comparison between 3D structure
# TODO accelerate Lipid selection per Slice in 2D and maybe 3D if possible, maybe precompute every lipid?
# TODO make a careful memory analysis to free more memory
# TODO incoportate new slices
# TODO have the documentation always open on the right on very big screens to fill emptyness
# TODO (if I have time) make mask hovering client side in javascript
# TODO when everything is stable, create a function that delete all pickle files and repickle everything automatically
# TODO write missing docstrings
