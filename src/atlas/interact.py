"""Module containing logic for GUI based interaction with Atlas."""
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from typing import Generator

import playwright
from openai.types.conversations import ItemCreateParams
from openai.types.conversations import Message
from openai.types.responses.response_input_param import ResponseInputItemParam
from playwright.sync_api import Browser
from playwright.sync_api import BrowserContext
from playwright.sync_api import Page

from playwright.sync_api import sync_playwright
from pynput.keyboard import Controller
from pynput.keyboard import Key
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from atlas._typing import PlannedConversation
from atlas.constants import ATLAS_APP_EXECUTABLE_PATH
from atlas.constants import DATA_FOLDER

# options: Options = Options()
# options.binary_location = ATLAS_APP_EXECUTABLE_PATH.as_posix()

# driver: webdriver.Chrome = webdriver.Chrome(options=options)


def run_conversation(planned_items: ItemCreateParams) -> None:
    PlannedConversation.validate_python(planned_items)

    with sync_atlas_browser() as browser:
        browser.new_page()
        for item in planned_items["items"]:
            item: ResponseInputItemParam


def enter_prompt(browser: Browser) -> None:
    """Enters a prompt to the Atlas """

@contextmanager
def sync_atlas_browser(**kwargs: Any) -> Generator[BrowserContext, None, None]:
    """Opens a new session of Atlas."""
    tempdir: str = tempfile.mkdtemp()
    with sync_playwright() as p:
        print("In playwright sync")
        browser: BrowserContext = p.chromium.launch_persistent_context(
            executable_path=ATLAS_APP_EXECUTABLE_PATH,
            headless=False,
            viewport=None,
            no_viewport=True,
            user_data_dir=tempdir,
            args=["--new-window"],
            **kwargs
        )
        print("browser instantiated")
        yield browser


if __name__ == "__main__":
    # time.sleep(5)
    # print("Before get")
    # driver.get("https://www.google.com")
    # print("After get")
    # time.sleep(5)
    # driver.quit()

    keyboard: Controller = Controller()
    with sync_atlas_browser() as context:
        print("Before Trace")
        context.tracing.start()
        context.new_page()
        print("During Trace")
        time.sleep(1)
        print("Before Type")
        keyboard.type("Please open google.com")
        keyboard.press(Key.enter)
        time.sleep(.01)
        keyboard.release(Key.enter)
        print("After Type")
        path: Path = DATA_FOLDER / "trace.zip"
        context.tracing.stop(path=path)
        print("After Trace")
        context.close()
        print("After close")



