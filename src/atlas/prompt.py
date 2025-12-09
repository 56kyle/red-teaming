"""Module containing logic for interacting with an Atlas conversation's prompts."""

from __future__ import annotations

from typing import Any
from typing import Generator

from loguru import logger

from atlas.accessibility import AXUIElementRef
from atlas.accessibility import ax_get_attribute
from atlas.accessibility import ax_perform_action
from atlas.accessibility import ax_set_attribute
from atlas.accessibility import find_live
from atlas.accessibility import find_live_by_subrole
from atlas.accessibility import find_live_first
from atlas.accessibility.api import ax_get_children
from atlas.interface import get_atlas_main
from atlas.interface import get_atlas_prompt_send_button
from atlas.interface import get_atlas_prompt_text_entry
from atlas.interface import get_atlas_ui
from atlas.interface import get_atlas_window


def is_prompt_loading() -> AXUIElementRef:
    """Returns whether the latest atlas non-user prompt is still in progress of generation."""
    atlas_root: AXUIElementRef = get_atlas_ui()
    atlas_window: AXUIElementRef | None = get_atlas_window(atlas_root)
    if atlas_window is None:
        raise ValueError("Failed to find atlas window")

    atlas_main: AXUIElementRef | None = find_live_by_subrole(atlas_window, "AXLandmarkMain", maximum_depth=25)
    if atlas_main is None:
        raise ValueError("Failed to find atlas main focused tab main landmark")
    logger.info("Found main landmark")
    return _is_ready_for_next_prompt(atlas_main)


def _is_ready_for_next_prompt(starting_element: AXUIElementRef) -> bool:
    """Returns whether the article is loading or not.

    Expects the starting element to be the main landmark present when not in a sidebar / etc.
    """
    latest_article: AXUIElementRef = _get_latest_article(starting_element)
    children: list[AXUIElementRef] = ax_get_children(latest_article)
    if len(children) != 2:
        raise ValueError(f"Article has unexpected number of children: {len(children)}")
    heading: AXUIElementRef = children[0]
    content: AXUIElementRef = children[1]

    heading_title: Any = ax_get_attribute(heading, "AXTitle")
    if str(heading_title) != "ChatGPT said:":
        logger.info("Waiting for chatgpt response to begin")
        return False

    return _find_copy_button(content) is not None


def find_articles(starting_element: AXUIElementRef, maximum_depth: int = 10) -> list[AXUIElementRef]:
    """Find all articles in the live hierarchy."""
    return find_live(starting_element, _is_article, maximum_depth)


def _is_article(element: AXUIElementRef) -> bool:
    """Returns whether the provided element is an article."""
    role: Any | None = ax_get_attribute(element, "AXSubrole")
    return role == "AXDocumentArticle"


def _get_latest_article(starting_element: AXUIElementRef) -> AXUIElementRef:
    """Returns the latest article in the live hierarchy."""
    articles: list[AXUIElementRef] = find_articles(starting_element)
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


def send_prompt(value: str) -> AXUIElementRef:
    """Sends the provided value as a prompt."""
    atlas_root: AXUIElementRef = get_atlas_ui()
    atlas_window: AXUIElementRef = get_atlas_window(atlas_root)
    atlas_main: AXUIElementRef = get_atlas_main(atlas_window)
    set_prompt_text(atlas_main, value=value)
    press_send_prompt_button(atlas_main)


def set_prompt_text(starting_element: AXUIElementRef, value: str) -> None:
    """Finds the Atlas text area and sets its value directly."""
    atlas_prompt_text_entry: AXUIElementRef | None = get_atlas_prompt_text_entry(starting_element)
    if atlas_prompt_text_entry is None:
        raise RuntimeError(f"Unable to find prompt text area within provided starting element: {starting_element}")

    focus_result: bool = ax_set_attribute(atlas_prompt_text_entry, "AXFocused", True)
    logger.debug(f"Focus result: {focus_result}")

    value_result: bool = ax_set_attribute(atlas_prompt_text_entry, "AXValue", value)
    logger.debug(f"Set value result: {value_result}")


def press_send_prompt_button(starting_element: AXUIElementRef) -> None:
    """Finds the prompt send button reference and presses it."""
    atlas_prompt_send_button: AXUIElementRef | None = get_atlas_prompt_send_button(starting_element)
    if atlas_prompt_send_button is None:
        raise RuntimeError(f"Unable to find prompt button within provided starting element: {starting_element}")
    press_result: bool = ax_perform_action(atlas_prompt_send_button, "AXPress")
    logger.debug(f"Press result: {press_result}")


if __name__ == "__main__":
    is_prompt_loading()
