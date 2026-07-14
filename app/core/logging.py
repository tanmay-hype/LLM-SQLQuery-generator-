import logging 
import sys

logger = logging.getLogger(__name__)

def configure_logging() -> None:
    """
    Configures logging for the application.
    """
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)-8s | "
            "%(name)s | "
            "%(message)s"
        ),
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
    )