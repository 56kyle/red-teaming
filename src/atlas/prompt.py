"""Module containing logic for interacting with an Atlas conversation's prompts."""

from __future__ import annotations

from typing import Any, TypedDict
from typing import Generator

from loguru import logger

from atlas.accessibility import ax_get_attribute
from atlas.accessibility import find_live
from atlas.accessibility import find_live_by_subrole
from atlas.accessibility import find_live_first
from atlas.accessibility.api import ax_get_children
from atlas.accessibility.predicates import create_live_subrole_predicate
from atlas.interface import get_atlas_ui
from atlas.interface import get_atlas_window


try:
    from ApplicationServices import (
        AXUIElementCopyAttributeValue,
        AXUIElementCopyAttributeNames,
        AXUIElementCreateApplication,
        AXUIElementCreateSystemWide,
        AXValueGetValue,
        kAXValueTypeCGPoint,
        kAXValueTypeCGSize,
    )
    from Cocoa import (
        NSApplicationActivationPolicyRegular,
        NSWorkspace,
    )
except ImportError as import_error:
    logger.error(f"Failed to import required macOS frameworks: {import_error}")
    raise

AXUIElementRef = Any


class PointDictionary(TypedDict):
    x: float
    y: float


class SizeDictionary(TypedDict):
    width: float
    height: float


def find_articles(starting_element: AXUIElementRef, maximum_depth: int = 10) -> list[AXUIElementRef]:
    """Find all articles in the live hierarchy."""
    return find_live(starting_element, create_live_subrole_predicate("AXDocumentArticle"), maximum_depth)


def get_latest_article(starting_element: AXUIElementRef) -> AXUIElementRef:
    """Returns the latest article in the live hierarchy."""
    articles: list[AXUIElementRef] = find_articles(starting_element)
    return articles[-1]


def is_ready_for_next_prompt(starting_element: AXUIElementRef) -> bool:
    """Returns whether the article is loading or not."""
    latest_article: AXUIElementRef = get_latest_article(starting_element)
    children: list[AXUIElementRef] = ax_get_children(latest_article)
    if len(children) != 2:
        raise ValueError(f"Article has unexpected number of children: {len(children)}")
    heading: AXUIElementRef = children[0]
    content: AXUIElementRef = children[1]

    heading_title: Any = ax_get_attribute(heading, "AXTitle")
    if str(heading_title) != "ChatGPT said:":
        logger.info("Waiting for chatgpt response to begin")
        return False

    return find_copy_button(content) is not None


def find_copy_button(starting_element: AXUIElementRef) -> AXUIElementRef | None:
    """Returns the copy button in the live hierarchy."""
    return find_live_first(starting_element, _is_copy_button)


def _is_copy_button(element: AXUIElementRef) -> bool:
    """Returns whether the passed element is the copy button."""
    role: Any | None = ax_get_attribute(element, "AXRole")
    description: Any | None = ax_get_attribute(element, "AXDescription")
    return role == "AXCheckBox" and description == "Copy"


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
    present: bool = is_ready_for_next_prompt(atlas_main)
    logger.info(present)
    while True:
        new_present = is_ready_for_next_prompt(atlas_main)
        if new_present != present:
            present: bool = new_present
            logger.info(present)


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


if __name__ == "__main__":
    is_prompt_loading()
    # print(get_text(get_atlas_ui()))
