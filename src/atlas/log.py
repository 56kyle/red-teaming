"""Module containing logic for logging used throughout the atlas package."""
from pathlib import Path

from loguru import logger

from atlas.constants import APP_START_TIME
from atlas.constants import USER_LOG_FOLDER
from atlas.constants import _FILE_SAFE_DATETIME_FORMAT


_FILE_SAFE_DATETIME_SLUG: str = APP_START_TIME.strftime(_FILE_SAFE_DATETIME_FORMAT)

LOG_PATH: Path = USER_LOG_FOLDER / f"log_{_FILE_SAFE_DATETIME_SLUG}.log"


logger.add(LOG_PATH, serialize=True)
