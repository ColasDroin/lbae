# TO CORRECT: https://dev.to/codemouse92/dead-simple-python-project-structure-and-imports-38c6
import logging

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
from lbae import index

server = index.app.server

# Run the app locally
if __name__ == "__main__":
    index.run()

# To run the app from the server, use the following command in the base lbae folder:
# gunicorn main:server -b:8050 --workers=1

