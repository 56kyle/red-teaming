"""Module containing utilities for automating prompt entry into Atlas browser."""
import subprocess
import time
from pathlib import Path
from typing import Any

from loguru import logger
from openai.types.conversations import ItemCreateParams
from openai.types.responses import ResponseInputItemParam
from pynput.keyboard import Controller
from pynput.keyboard import Key

from atlas.constants import ATLAS_APP_EXECUTABLE_PATH
from atlas.demo import load_planned_conversation


# Constants for wait strategies
_MAX_BROWSER_STARTUP_WAIT_SECONDS: float = 15.0
_MAX_TAB_OPEN_WAIT_SECONDS: float = 5.0
_PROCESS_CHECK_INTERVAL_SECONDS: float = 0.1
_KEYBOARD_STABILIZATION_DELAY_SECONDS: float = 0.05


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
    check_interval: float = _PROCESS_CHECK_INTERVAL_SECONDS

    while elapsed_seconds < timeout_seconds:
        if not _is_process_alive(process):
            msg: str = (
                f"Browser process {process.pid} terminated unexpectedly "
                f"after {elapsed_seconds:.2f}s"
            )
            raise RuntimeError(msg)

        time.sleep(check_interval)
        elapsed_seconds = time.time() - start_time
        check_interval = min(check_interval * 1.2, 0.5)

    logger.debug(f"Browser stabilized after {elapsed_seconds:.2f}s startup wait")


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


def _send_new_tab_keyboard_command(keyboard: Controller) -> None:
    """Send the keyboard shortcut to open a new tab (Cmd+T on macOS)."""
    keyboard.press(Key.cmd)
    keyboard.press("t")
    keyboard.release("t")
    keyboard.release(Key.cmd)
    _wait_for_keyboard_stability()


def _open_new_tab(max_retries: int = 3) -> None:
    """Open a new tab with exponential backoff retry logic."""
    keyboard: Controller = Controller()

    for attempt in range(max_retries):
        try:
            logger.debug(f"Opening new tab (attempt {attempt + 1}/{max_retries})")
            _send_new_tab_keyboard_command(keyboard)
            logger.debug("New tab opened")
            return

        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} to open tab failed: {e}")
            if attempt == max_retries - 1:
                msg: str = f"Failed to open new tab after {max_retries} attempts"
                raise RuntimeError(msg)

            retry_wait: float = 0.5 * (2 ** attempt)
            logger.debug(f"Waiting {retry_wait:.2f}s before retry")
            time.sleep(retry_wait)


def _enter_text_with_keyboard(text: str, delay_per_char: float = 0.02) -> None:
    """Enter text character-by-character into the focused browser window."""
    keyboard: Controller = Controller()

    for char in text:
        keyboard.type(char)
        time.sleep(delay_per_char)

    _wait_for_keyboard_stability(delay_per_char)
    logger.debug(f"Entered {len(text)} characters")


def _submit_prompt(min_wait_seconds: float = 0.05) -> None:
    """Submit the current prompt by pressing Enter with stabilization buffer."""
    keyboard: Controller = Controller()
    keyboard.press(Key.enter)
    keyboard.release(Key.enter)
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


def _filter_user_messages(
    items: list[ResponseInputItemParam],
) -> list[ResponseInputItemParam]:
    """Filter items to only include messages with role='user'."""
    user_messages: list[ResponseInputItemParam] = [
        item for item in items if item.get("role") == "user"
    ]
    logger.debug(f"Filtered {len(items)} items to {len(user_messages)} user messages")
    return user_messages


def _process_user_messages(
    user_messages: list[ResponseInputItemParam],
    wait_after_submit: float,
) -> None:
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


def run_auto_prompt(
    conversation_path: Path,
    wait_after_submit: float = 2.0,
    launch_browser_automatically: bool = True,
) -> subprocess.Popen[bytes] | None:
    """Launch browser, open tab, and automatically submit prompts from a conversation file.

    Optionally launches the browser, opens a new tab, loads conversation messages, and
    enters each user message as keyboard input to the browser.
    """
    logger.info(f"Starting auto_prompt with conversation: {conversation_path}")

    if not conversation_path.exists():
        msg: str = f"Conversation file not found at {conversation_path}"
        raise FileNotFoundError(msg)

    browser_process: subprocess.Popen[bytes] | None = None
    if launch_browser_automatically:
        browser_process = _launch_browser()
    else:
        logger.info("Skipping browser launch; assuming browser is already open")

    try:
        _open_new_tab()

        logger.info("Loading planned conversation from file")
        params: ItemCreateParams = load_planned_conversation(conversation_path)
        items: list[ResponseInputItemParam] = list(params.get("items", []))

        if not items:
            logger.warning("No conversation items found in file")
            return browser_process

        user_messages: list[ResponseInputItemParam] = _filter_user_messages(items)

        if not user_messages:
            logger.warning("No user messages found in conversation")
            return browser_process

        _process_user_messages(user_messages, wait_after_submit)
        logger.info("Auto-prompt completed successfully")

    except Exception as e:
        logger.error(f"Error during auto-prompt execution: {e}", exc_info=True)
        raise

    return browser_process


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
