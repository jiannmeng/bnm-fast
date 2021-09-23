from pathlib import Path
import logging
from rich.logging import RichHandler

ROOT_FOLDER = Path(__file__).resolve().parent.parent
XML_FOLDER = ROOT_FOLDER / "xml"
OUTPUT_FOLDER = ROOT_FOLDER / "output"

logging.basicConfig(
    level="DEBUG",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("rich")
