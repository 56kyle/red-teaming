"""Module containing utilities for automating prompt entry into Atlas browser."""
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from typing import Optional

import pyperclip
from loguru import logger
from openai.types.responses import ResponseInputItemParam
from pynput.keyboard import Controller
from pynput.keyboard import Key
from pynput.keyboard import KeyCode

from atlas.constants import ATLAS_APP_EXECUTABLE_PATH
from atlas.constants import DATA_FOLDER
from atlas.demo import get_user_messages_from_conversation


# Constants for wait strategies
_MAX_BROWSER_STARTUP_WAIT_SECONDS: float = 15.0
_MAX_TAB_OPEN_WAIT_SECONDS: float = 5.0
_PROCESS_CHECK_INTERVAL_SECONDS: float = 0.01
_KEYBOARD_STABILIZATION_DELAY_SECONDS: float = 0.05
_WINDOW_FOCUS_DELAY_SECONDS: float = 0.5

keyboard: Controller = Controller()


def _is_process_alive(process: subprocess.Popen[bytes]) -> bool:
    """Check if a subprocess process is still running."""
    return process.poll() is None


def _wait_for_browser_startup(
    process: subprocess.Popen[bytes],
    timeout_seconds: float = _MAX_BROWSER_STARTUP_WAIT_SECONDS,
) -> None:
    """Wait for browser process to stabilize with exponential backoff checks.

    Monitors the process with exponential backoff (0.1s to 0.5s intervals) up to the
    timeout to ensure it remains alive and responsive.
    """
    start_time: float = time.time()
    elapsed_seconds: float = 0.0

    while elapsed_seconds < timeout_seconds and not _is_process_alive(process):
        time.sleep(_PROCESS_CHECK_INTERVAL_SECONDS)
        elapsed_seconds = time.time() - start_time

    if not _is_process_alive(process):
        msg: str = f"Browser process {process.pid} terminated unexpectedly after {elapsed_seconds:.2f}s"
        raise RuntimeError(msg)

    logger.debug(f"Browser stabilized after {elapsed_seconds:.2f}s startup wait")


def _focus_browser_window() -> None:
    """Focus the browser window to prepare it for keyboard input.

    On macOS, uses osascript to bring the ChatGPT Atlas application to the foreground.
    On other platforms, relies on system window management.
    """
    if "darwin" in sys.platform:
        try:
            applescript: str = 'tell application "ChatGPT Atlas" to activate'
            subprocess.run(
                ["osascript", "-e", applescript],
                check=True,
                capture_output=True,
                timeout=5,
            )
            logger.debug("Browser window focused via osascript")
            time.sleep(_WINDOW_FOCUS_DELAY_SECONDS)
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to focus window via osascript: {e}")
        except FileNotFoundError:
            logger.warning("osascript not found; cannot focus window")
        except subprocess.TimeoutExpired:
            logger.warning("osascript command timed out")
    else:
        logger.debug(f"Window focusing not implemented for platform: {sys.platform}")


def _launch_browser() -> subprocess.Popen[bytes]:
    """Launch the Atlas browser executable and verify startup stabilization."""
    logger.info(f"Launching browser from {ATLAS_APP_EXECUTABLE_PATH}")

    if not ATLAS_APP_EXECUTABLE_PATH.exists():
        msg: str = f"Atlas executable not found at {ATLAS_APP_EXECUTABLE_PATH}"
        raise FileNotFoundError(msg)

    process: subprocess.Popen[bytes] = subprocess.Popen(
        [str(ATLAS_APP_EXECUTABLE_PATH)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    logger.info(f"Browser launched with PID {process.pid}")
    _wait_for_browser_startup(process)

    return process


def _wait_for_keyboard_stability(delay_seconds: float = _KEYBOARD_STABILIZATION_DELAY_SECONDS) -> None:
    """Wait for keyboard system to stabilize after input."""
    time.sleep(delay_seconds)


def _open_new_tab() -> None:
    """Open a new tab with exponential backoff retry logic."""
    __press_and_release_together(Key.cmd, "t")
    _wait_for_keyboard_stability()
    logger.debug("New tab opened")


def _enter_text_with_keyboard(text: str, delay_per_char: float = 0.02) -> None:
    """Enter text character-by-character into the focused browser window."""
    pyperclip.copy(text)
    __press_and_release_together(Key.cmd, "v")

    _wait_for_keyboard_stability(delay_per_char)
    logger.debug(f"Entered {len(text)} characters")


def __press_and_release_together(*keys: KeyCode | str) -> None:
    """Presses all provided keys together in order then releases all."""
    for key in keys:
        keyboard.press(key)
    time.sleep(.1)
    for key in reversed(keys):
        keyboard.release(key)


def _submit_prompt(min_wait_seconds: float = 0.05) -> None:
    """Submit the current prompt by pressing Enter with stabilization buffer."""
    keyboard.tap(Key.enter)
    _wait_for_keyboard_stability(min_wait_seconds)
    logger.debug("Prompt submitted")


def _extract_message_text(message_item: ResponseInputItemParam) -> str | None:
    """Extract text content from a message item, returning None if unavailable."""
    try:
        content: Any = message_item.get("content")
        if isinstance(content, list) and len(content) > 0:
            text: str | None = content[0].get("text")
            return text
    except (KeyError, TypeError, IndexError) as e:
        logger.warning(f"Failed to extract text from message item: {e}")

    return None


def _process_user_messages(user_messages: list[ResponseInputItemParam], wait_after_submit: float) -> None:
    """Process and submit each user message as keyboard input.

    Extracts text from each message, enters it via keyboard, and submits it.
    """
    logger.info(f"Processing {len(user_messages)} user messages")

    for idx, message in enumerate(user_messages, start=1):
        text: str | None = _extract_message_text(message)

        if text is None:
            logger.warning(f"Skipping message {idx}: no text content")
            continue

        logger.info(f"Entering message {idx}/{len(user_messages)}")
        _enter_text_with_keyboard(text)
        _submit_prompt()

        if idx < len(user_messages):
            logger.debug(f"Waiting {wait_after_submit}s before next prompt")
            time.sleep(wait_after_submit)


def run_auto_prompt(conversation_path: Path, wait_after_submit: float = 2.0) -> subprocess.Popen[bytes] | None:
    """Launch browser, open tab, and automatically submit prompts from a conversation file.

    Optionally launches the browser, opens a new tab, loads conversation messages, and
    enters each user message as keyboard input to the browser.
    """
    logger.info(f"Starting auto_prompt with conversation: {conversation_path}")

    if not conversation_path.exists():
        msg: str = f"Conversation file not found at {conversation_path}"
        raise FileNotFoundError(msg)

    browser_process: subprocess.Popen[bytes] | None = _launch_browser()

    try:
        # _open_new_tab()
        user_messages: Optional[list[ResponseInputItemParam]] = get_user_messages_from_conversation(
            path=conversation_path
        )

        if user_messages is None:
            logger.warning("No user messages found in conversation")
            return browser_process

        _process_user_messages(user_messages, wait_after_submit)
        logger.info("Auto-prompt completed successfully")

    except Exception as e:
        logger.error(f"Error during auto-prompt execution: {e}", exc_info=True)
        raise


def cleanup_browser_process(process: subprocess.Popen[bytes]) -> None:
    """Terminate a browser process gracefully, forcing kill if necessary."""
    if process is None:
        return

    logger.info(f"Terminating browser process {process.pid}")
    try:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning("Browser process did not terminate; forcing kill")
            process.kill()
            process.wait()
    except Exception as e:
        logger.error(f"Error terminating browser process: {e}")


if __name__ == "__main__":
    path: Path = DATA_FOLDER / "prompt_ideas" / "standard_ss13_02.json"
    run_auto_prompt(conversation_path=path, wait_after_submit=5.0)
