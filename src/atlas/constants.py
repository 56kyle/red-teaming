"""Module containing constants used throughout the atlas package."""

import datetime

from pathlib import Path

from platformdirs import user_cache_path
from platformdirs import user_config_path
from platformdirs import user_log_path


_FILE_SAFE_DATETIME_FORMAT: str = "%Y-%m-%dT%H-%M-%SZ"


APP_NAME: str = "atlas"
APP_AUTHOR: str = "56Kyle"
APP_START_TIME: datetime.datetime = datetime.datetime.now(tz=datetime.timezone.utc)

USER_CACHE_FOLDER: Path = user_cache_path(appname=APP_NAME, appauthor=APP_AUTHOR, ensure_exists=True)
USER_CONFIG_FOLDER: Path = user_config_path(appname=APP_NAME, appauthor=APP_AUTHOR, ensure_exists=True)
USER_LOG_FOLDER: Path = user_log_path(appname=APP_NAME, appauthor=APP_AUTHOR, ensure_exists=True)


ATLAS_APP_NAME: str = "com.openai.atlas"
ATLAS_APP_AUTHOR: str = "openai"
ATLAS_CACHE_FOLDER: Path = user_cache_path(appname=ATLAS_APP_NAME, appauthor=ATLAS_APP_AUTHOR)
ATLAS_CONFIG_FOLDER: Path = user_config_path(appname=ATLAS_APP_NAME, appauthor=ATLAS_APP_AUTHOR)

ATLAS_APP_EXECUTABLE_PATH: Path = Path("/Applications/ChatGPT Atlas.app")

PACKAGE_FOLDER: Path = Path(__file__).parent
REPO_FOLDER: Path = PACKAGE_FOLDER.parent.parent
DATA_FOLDER: Path = REPO_FOLDER / "data"
