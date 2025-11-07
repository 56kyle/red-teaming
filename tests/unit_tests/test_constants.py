import sys

import pytest

from atlas.constants import ATLAS_CACHE_FOLDER
from atlas.constants import ATLAS_CONFIG_FOLDER


def test_mac_constants_match() -> None:
    if "darwin" not in sys.platform:
        pytest.skip("Not using MacOS")

    assert ATLAS_CACHE_FOLDER.exists()
    assert ATLAS_CONFIG_FOLDER.exists()
