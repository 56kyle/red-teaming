"""Module containing constants used throughout the atlas package."""
import datetime

from pathlib import Path

from platformdirs import user_cache_path
from platformdirs import user_config_path
from platformdirs import user_log_path


_FILE_SAFE_DATETIME_FORMAT: str = "%Y-%m-%dT%H-%M-%SZ"


APP_NAME: str = "atlas"
APP_AUTHOR: str = "56Kyle"
APP_START_TIME: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

USER_CACHE_FOLDER: Path = user_cache_path(appname=APP_NAME, appauthor=APP_AUTHOR, ensure_exists=True)
USER_CONFIG_FOLDER: Path = user_config_path(appname=APP_NAME, appauthor=APP_AUTHOR, ensure_exists=True)
USER_LOG_FOLDER: Path = user_log_path(appname=APP_NAME, appauthor=APP_AUTHOR, ensure_exists=True)
