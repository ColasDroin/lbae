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


#! Create a function that delete all pickle files and repickle everything automatically

# Run the app locally
if __name__ == "__main__":
    logging.info("Starting app" + logmem())
    index.run()

# To run the app from the server, use the following command in the base lbae folder:
# gunicorn main:server -b:8050 --workers=1

# TODO debug region selection
# TODO update lipid list to have all lipids in dropdown
# TODO write missing docstrings
# TODO update layout with react grid where needed
# TODO accelerate Lipid selection per Slice in 2D and maybe 3D if possible, maybe precompute every lipid?
# TODO make a careful memory analysis
# TODO have the documentation always open on the left on very big screens
# TODO make mask hovering client side
