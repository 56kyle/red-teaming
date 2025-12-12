"""Module containing logic for interacting with an Atlas conversation's prompts."""

from __future__ import annotations

import time
from typing import Any
from typing import Generator

from loguru import logger
from openai.types.conversations import ItemCreateParams

from atlas.accessibility import AXUIElementRef
from atlas.accessibility import ax_get_action_names
from atlas.accessibility import ax_get_attribute
from atlas.accessibility import ax_perform_action
from atlas.accessibility import ax_set_attribute
from atlas.accessibility import find_live
from atlas.accessibility import find_live_by_subrole
from atlas.accessibility import find_live_first
from atlas.accessibility.api import ax_get_children
from atlas.hierarchy_broad import save_state
from atlas.interface import _get_atlas_main
from atlas.interface import get_atlas_main
from atlas.interface import get_atlas_main_or_window
from atlas.interface import get_atlas_prompt_send_button
from atlas.interface import get_atlas_prompt_stop_button
from atlas.interface import get_atlas_prompt_text_entry
from atlas.interface import get_atlas_ui
from atlas.interface import _get_atlas_window
from atlas.interface import get_atlas_window
from atlas.interface import press_enter_in_atlas


DEFAULT_PROMPT_CHECK_DELAY: float = 0.3
DEFAULT_PROMPT_TIMEOUT: float = 60.0


def is_prompt_loading() -> AXUIElementRef:
    """Returns whether the latest atlas non-user prompt is still in progress of generation."""
    atlas_root: AXUIElementRef = get_atlas_ui()
    atlas_window: AXUIElementRef | None = _get_atlas_window(atlas_root)
    if atlas_window is None:
        raise ValueError("Failed to find atlas window")

    atlas_main: AXUIElementRef | None = find_live_by_subrole(atlas_window, "AXLandmarkMain", maximum_depth=30)
    if atlas_main is None:
        return True

    composer_stop_button: AXUIElementRef | None = get_atlas_prompt_stop_button(atlas_main)

    return composer_stop_button is not None


def is_ready_to_submit_text_entry() -> bool:
    """Returns whether Atlas is ready to submit the current text entry."""
    text_entry: AXUIElementRef | None = get_atlas_prompt_text_entry()
    if text_entry is None:
        return False

    text_value: Any | None = ax_get_attribute(text_entry, "AXValue")
    if text_value is None:
        return False

    submit_button: AXUIElementRef | None = get_atlas_prompt_send_button()
    if submit_button is None:
        return False

    return True


def is_ready_for_next_prompt() -> bool:
    """Returns whether the article is loading or not."""
    closest_element: AXUIElementRef = get_atlas_main_or_window()

    articles: list[AXUIElementRef] = find_articles(closest_element)
    if len(articles) == 0:
        logger.debug(f"Failed to find any articles")
        return False

    copy_button: AXUIElementRef | None = _find_copy_button(articles[-1])
    if copy_button is None:
        return False

    composer_stop_button: AXUIElementRef | None = get_atlas_prompt_stop_button(closest_element)
    return composer_stop_button is None


def find_articles(starting_element: AXUIElementRef, maximum_depth: int = 30) -> list[AXUIElementRef]:
    """Find all articles in the live hierarchy."""
    return find_live(starting_element, _is_article, maximum_depth)


def _is_article(element: AXUIElementRef) -> bool:
    """Returns whether the provided element is an article."""
    role: Any | None = ax_get_attribute(element, "AXSubrole")
    return role == "AXDocumentArticle"


def get_latest_article() -> AXUIElementRef | None:
    """Returns the latest article in the live hierarchy."""
    closest_element: AXUIElementRef = get_atlas_main_or_window()
    return _get_latest_article(closest_element)


def _get_latest_article(starting_element: AXUIElementRef) -> AXUIElementRef | None:
    """Returns the latest article in the live hierarchy."""
    articles: list[AXUIElementRef] = find_articles(starting_element)
    if len(articles) == 0:
        return None
    return articles[-1]


def _find_copy_button(starting_element: AXUIElementRef) -> AXUIElementRef | None:
    """Returns the copy button in the live hierarchy."""
    return find_live_first(starting_element, __is_copy_button)


def __is_copy_button(element: AXUIElementRef) -> bool:
    """Returns whether the passed element is the copy button."""
    role: Any | None = ax_get_attribute(element, "AXRole")
    description: Any | None = ax_get_attribute(element, "AXDescription")
    return role == "AXCheckBox" and description == "Copy"


def get_text(element: AXUIElementRef) -> str:
    """Returns all text within the provided element exhaustively.

    Does not account for formatting done through UI placement or images.
    """
    return "".join(_iter_text(element))


def _iter_text(element: AXUIElementRef) -> Generator[str, None, None]:
    """Returns the text of the given element."""
    role: Any | None = ax_get_attribute(element, "AXRole")
    for child in ax_get_children(element):
        yield from _iter_text(child)
    if str(role) == "AXStaticText":
        value: Any | None = ax_get_attribute(element, "AXValue")
        yield str(value)


def send_prompt(value: str, timeout: float = DEFAULT_PROMPT_TIMEOUT) -> str:
    """Sends the provided value as a prompt."""
    logger.debug("Sending prompt...")
    set_prompt_text(value)
    submit_entered_prompt()
    send_time: float = time.time()
    while not is_ready_for_next_prompt():
        if time.time() - send_time > timeout:
            raise TimeoutError(f"Timed out while waiting for prompt to load for {timeout} seconds.")
    return get_prompt_response()


def set_prompt_text(value: str) -> None:
    """Finds the Atlas text area and sets its value directly."""
    shortened_value = value[:80] if len(value) > 80 else value
    logger.debug(f"Attempting to set prompt text:\n {shortened_value}")
    atlas_prompt_text_entry: AXUIElementRef | None = get_atlas_prompt_text_entry()
    if atlas_prompt_text_entry is None:
        raise RuntimeError(f"Unable to find prompt text area.")
    logger.debug(ax_get_action_names(atlas_prompt_text_entry))

    focus_result: bool = ax_set_attribute(atlas_prompt_text_entry, "AXFocused", True)
    logger.debug(f"Focus result: {focus_result}")

    value_result: bool = ax_set_attribute(atlas_prompt_text_entry, "AXValue", value)
    logger.debug(f"Set value result: {value_result}")
    logger.debug("Done setting prompt text.")


def submit_entered_prompt() -> None:
    """Submits the entered value as a prompt in Atlas."""
    text_entry: AXUIElementRef | None = get_atlas_prompt_text_entry()
    if text_entry is None:
        raise RuntimeError(f"Unable to find prompt text entry.")

    ax_set_attribute(text_entry, "AXFocused", True)
    press_enter_in_atlas()


def get_prompt_response() -> str:
    """Returns the text found within the Atlas prompt's response."""
    response_article: AXUIElementRef | None = get_latest_article()
    if response_article is None:
        raise RuntimeError(f"Unable to find latest article.")
    return get_text(response_article)


def press_send_prompt_button() -> None:
    """Finds the prompt send button reference and presses it."""
    atlas_prompt_send_button: AXUIElementRef | None = get_atlas_prompt_send_button()
    if atlas_prompt_send_button is None:
        raise RuntimeError(f"Unable to find prompt button.")
    ax_set_attribute(atlas_prompt_send_button, "AXFocused", True)
    ax_set_attribute(atlas_prompt_send_button, "AXSelected", True)
    logger.debug(ax_get_action_names(atlas_prompt_send_button))
    press_result: bool = ax_perform_action(atlas_prompt_send_button, "AXPress")
    logger.debug(f"Press result: {press_result}")
    time.sleep(.05)


if __name__ == "__main__":
    load_state: bool = is_prompt_loading()
    logger.info(load_state)
    while True:
        state: bool = is_prompt_loading()
        if load_state != state:
            load_state = state
            logger.info(state)
