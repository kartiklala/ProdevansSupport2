from loguru import logger
import sys
from pathlib import Path

LOG_PATH = Path("backend_logs.log")

logger.remove()
logger.add(sys.stdout, level="DEBUG")
logger.add(LOG_PATH, rotation="5 MB", level="DEBUG")

def get_logger():
    return logger
