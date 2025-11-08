"""Module containing logic for GUI based interaction with Atlas."""
import time
from contextlib import contextmanager
from typing import Any
from typing import Generator

import playwright
from openai.types.conversations import ItemCreateParams
from openai.types.conversations import Message
from openai.types.responses.response_input_param import ResponseInputItemParam
from playwright.sync_api import Browser

from playwright.sync_api import sync_playwright

from atlas._typing import PlannedConversation
from atlas.constants import ATLAS_APP_EXECUTABLE_PATH


def run_conversation(planned_items: ItemCreateParams) -> None:
    PlannedConversation.validate_python(planned_items)

    with sync_atlas_browser() as browser:
        browser.new_page()
        for item in planned_items["items"]:
            item: ResponseInputItemParam


def enter_prompt(browser: Browser) -> None:
    """Enters a prompt to the Atlas """

@contextmanager
def sync_atlas_browser(**kwargs: Any) -> Generator[Browser, None, None]:
    """Opens a new session of Atlas."""
    with sync_playwright() as p:
        browser: Browser = p.chromium.launch(executable_path=ATLAS_APP_EXECUTABLE_PATH, headless=False, **kwargs)
        yield browser


if __name__ == "__main__":
    with sync_atlas_browser() as browser:
        time.sleep(5)
        browser.new_page()
        time.sleep(5)


