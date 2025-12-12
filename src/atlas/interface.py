"""Module containing logic for interacting with the Atlas user interface."""

from __future__ import annotations

import time
from typing import Any

from loguru import logger

from atlas.accessibility import AXUIElementRef
from atlas.accessibility import ApplicationInfo
from atlas.accessibility import ax_get_attribute
from atlas.accessibility import ax_get_attribute_names
from atlas.accessibility import ax_perform_action
from atlas.accessibility import find_live
from atlas.accessibility import find_live_first

from atlas.app import get_or_create_atlas_application


try:
    from ApplicationServices import AXUIElementCreateApplication
    from Quartz import (
        CGEventCreateKeyboardEvent,
        CGEventPostToPid,
        kCGHIDEventTap
    )
except ImportError as import_error:
    logger.error(f"Failed to import required macOS frameworks: {import_error}")
    raise

DEFAULT_TAB_DELAY: float = 0.5


def get_atlas_ui() -> AXUIElementRef:
    """Returns the live state of the atlas UI."""
    app_info: ApplicationInfo = get_or_create_atlas_application()
    atlas_root: AXUIElementRef = create_accessibility_element_for_application(app_info["process_id"])
    return atlas_root


def create_accessibility_element_for_application(process_id: int) -> AXUIElementRef:
    """Create an accessibility element reference for an application by process ID."""
    return AXUIElementCreateApplication(process_id)


def get_atlas_window() -> AXUIElementRef:
    """Returns the first valid atlas window reference.

    For Chromium-based apps, AXFocusedWindow/AXMainWindow are more reliable
    than AXWindows. Windows from AXWindows are validated to have attributes.
    """
    atlas_root: AXUIElementRef = get_atlas_ui()
    return _get_atlas_window(atlas_root)


def _get_atlas_window(app_element: AXUIElementRef) -> AXUIElementRef:
    """Returns the first valid atlas window reference."""
    # Try focused/main window first (more reliable for Chromium-based apps)
    for window_attr in ("AXFocusedWindow", "AXMainWindow"):
        window: Any | None = ax_get_attribute(app_element, window_attr)
        if window is not None:
            return window

    # Fall back to AXWindows array with validation
    windows: Any | None = ax_get_attribute(app_element, "AXWindows")
    if windows is not None:
        try:
            for i in range(len(windows)):
                window: AXUIElementRef = windows[i]
                # Validate window has attributes (Chromium windows may be stubs)
                if len(ax_get_attribute_names(window)) > 0:
                    return window
        except TypeError:
            pass

    raise RuntimeError(f"Could not find window reference: {app_element}")


def focus_atlas_window(element: AXUIElementRef) -> AXUIElementRef:
    """Focuses the atlas window reference."""
    ax_perform_action(element, "AXRaise")


def open_new_atlas_tab(starting_element: AXUIElementRef, delay: float = DEFAULT_TAB_DELAY) -> AXUIElementRef:
    """Finds the Atlas tab button and presses it."""
    new_tab_button: AXUIElementRef = _get_atlas_new_tab_button(starting_element)
    ax_perform_action(new_tab_button, "AXPress")
    time.sleep(delay)


def get_atlas_new_tab_button() -> AXUIElementRef:
    """Gets the Atlas new tab button starting from nothing."""
    atlas_root: AXUIElementRef = get_atlas_ui()
    return _get_atlas_new_tab_button(atlas_root)


def _get_atlas_new_tab_button(starting_element: AXUIElementRef) -> AXUIElementRef:
    """Returns the Atlas new tab button."""
    return find_live_first(starting_element, _is_atlas_new_tab_button, maximum_depth=20)


def _is_atlas_new_tab_button(element: AXUIElementRef) -> bool:
    """Returns True if the provided element is the new tab button."""
    role: Any | None = ax_get_attribute(element, "AXRole")
    description: Any | None = ax_get_attribute(element, "AXDescription")
    return str(role) == "AXButton" and str(description) == "New Tab"


def get_atlas_main() -> AXUIElementRef | None:
    """Returns the Atlas main web page dom reference if present."""
    atlas_window: AXUIElementRef = get_atlas_window()
    return _get_atlas_main(atlas_window)


def _get_atlas_main(window_element: AXUIElementRef) -> AXUIElementRef | None:
    """Returns the main atlas interface reference."""
    return find_live_first(window_element, _is_atlas_main, maximum_depth=20)


def _is_atlas_main(element: AXUIElementRef) -> bool:
    """Returns whether the provided element is a main atlas interface reference."""
    subrole: Any | None = ax_get_attribute(element, "AXSubrole")
    return subrole == "AXLandmarkMain"


def get_atlas_main_or_window() -> AXUIElementRef:
    """Returns the Atlas main or window element reference."""
    atlas_window: AXUIElementRef = get_atlas_window()
    atlas_main: AXUIElementRef | None = _get_atlas_main(atlas_window)
    closest_element: AXUIElementRef = atlas_main if atlas_main is not None else atlas_window
    return closest_element


def get_atlas_web_areas() -> AXUIElementRef | None:
    """Returns a list of Atlas web area references."""
    atlas_window: AXUIElementRef = get_atlas_window()
    if atlas_window is None:
        raise RuntimeError("No Atlas window found to search for web areas in.")
    return _get_atlas_web_areas(atlas_window)


def _get_atlas_web_areas(starting_element: AXUIElementRef) -> list[AXUIElementRef]:
    """Returns a list of atlas web area references."""
    return find_live(starting_element, _is_atlas_web_area, maximum_depth=20)


def _is_atlas_web_area(element: AXUIElementRef) -> bool:
    """Returns True if the element is the atlas web area."""
    result: AXUIElementRef = ax_get_attribute(element, "AXRole") == "AXWebArea"
    return result


def toggle_atlas_sidebar(starting_element: AXUIElementRef) -> None:
    """Opens the Atlas sidebar provided."""
    sidebar_button: AXUIElementRef = _get_atlas_sidebar_button(starting_element)
    ax_perform_action(sidebar_button, "AXEnable")


def get_atlas_sidebar_button() -> AXUIElementRef | None:
    """Returns the Atlas sidebar button."""
    atlas_window: AXUIElementRef = get_atlas_window()
    return _get_atlas_sidebar_button(atlas_window)


def _get_atlas_sidebar_button(starting_element: AXUIElementRef) -> AXUIElementRef | None:
    """Returns the Atlas sidebar button."""
    return find_live_first(starting_element, _is_atlas_sidebar_button, maximum_depth=20)


def _is_atlas_sidebar_button(element: AXUIElementRef) -> bool:
    """Returns True if the element is the Atlas sidebar button."""
    role: Any | None = ax_get_attribute(element, "AXRole")
    title: Any | None = ax_get_attribute(element, "AXTitle")
    description: Any | None = ax_get_attribute(element, "AXDescription")
    phrase_met: bool = str(title) == "Open sidebar" or str(description) == "Close sidebar"
    if phrase_met:
        return True
    return str(role) == "AXButton" and phrase_met


def get_atlas_sidebar() -> AXUIElementRef | None:
    """Returns the Atlas sidebar button."""
    atlas_window: AXUIElementRef = get_atlas_window()
    return _get_atlas_sidebar_button(atlas_window)


def _get_atlas_sidebar(starting_element: AXUIElementRef) -> AXUIElementRef | None:
    """Returns the Atlas sidebar reference."""
    return find_live_first(starting_element, _is_atlas_sidebar)


def _is_atlas_sidebar(element: AXUIElementRef) -> bool:
    """Returns True if the element is the Atlas sidebar."""
    title: str | None = ax_get_attribute(element, "AXTitle")
    subrole: str | None = ax_get_attribute(element, "AXSubrole")
    return str(title) == "Sidebar" and str(subrole) == "AXApplicationDialog"


def _get_sidebar_conversation_links(sidebar_element: AXUIElementRef) -> list[AXUIElementRef]:
    """Returns a list of sidebar conversation link references."""
    navigation_element: AXUIElementRef = _get_sidebar_navigation(sidebar_element)
    navigation_history_element: AXUIElementRef = _get_sidebar_navigation_history(navigation_element)
    history_link_elements: list[AXUIElementRef] = _find_all_navigation_history_links(navigation_history_element)
    return [ax_get_attribute(element, "AXURL") for element in history_link_elements]


def _get_sidebar_navigation(sidebar_element: AXUIElementRef) -> AXUIElementRef | None:
    """Returns the Atlas sidebar navigation reference."""
    return find_live_first(sidebar_element, _is_sidebar_navigation)


def _is_sidebar_navigation(element: AXUIElementRef) -> bool:
    """Returns True if the element is the Atlas sidebar navigation reference."""
    subrole: str | None = ax_get_attribute(element, "AXSubrole")
    description: str | None = ax_get_attribute(element, "AXDescription")
    return subrole == "AXLandmarkNavigation" and description == "Chat history"


def _get_sidebar_navigation_history(sidebar_navigation_element: AXUIElementRef) -> list[AXUIElementRef]:
    """Returns the Atlas sidebar navigation's history reference."""
    return find_live_first(sidebar_navigation_element, _is_sidebar_navigation)


def _is_sidebar_navigation_history(element: AXUIElementRef) -> bool:
    """Returns whether the given element is the Atlas sidebar navigation history reference."""
    dom_identifier: str | None = ax_get_attribute(element, "AXDOMIdentifier")
    return dom_identifier == "history"


def _find_all_navigation_history_links(navigation_history_element: AXUIElementRef) -> list[AXUIElementRef]:
    """Returns all Atlas sidebar history navigation link references."""
    return find_live(navigation_history_element, _is_navigation_history_link)


def _is_navigation_history_link(element: AXUIElementRef) -> bool:
    """Returns True if the element is an Atlas sidebar's navigation history link."""
    role: str | None = ax_get_attribute(element, "AXRole")
    url: str | None = ax_get_attribute(element, "AXURL")
    return role == "AXLink" and str(url).startswith("https://chatgpt.com/c/")


def get_atlas_prompt_text_entry() -> AXUIElementRef | None:
    """Returns the Atlas prompt text entry reference."""
    closest_element: AXUIElementRef = get_atlas_main_or_window()
    return _get_atlas_prompt_text_entry(closest_element)


def _get_atlas_prompt_text_entry(starting_element: AXUIElementRef) -> AXUIElementRef | None:
    """Returns the Atlas prompt entry reference."""
    return find_live_first(starting_element, _is_atlas_prompt_text_entry, maximum_depth=25)


def _is_atlas_prompt_text_entry(element: AXUIElementRef) -> bool:
    """Returns True if the element is the Atlas prompt entry reference.`"""
    dom_identifier: Any | None = ax_get_attribute(element, "AXDOMIdentifier")
    role_description: Any | None = ax_get_attribute(element, "AXRoleDescription")
    return str(dom_identifier) == "prompt-textarea" or str(role_description) == "text entry area"


def get_atlas_prompt_send_button() -> AXUIElementRef | None:
    """Returns the Atlas prompt send button reference."""
    closest_element: AXUIElementRef = get_atlas_main_or_window()
    atlas_thread_bottom: Any | None = get_atlas_thread_bottom()
    if atlas_thread_bottom is not None:
        closest_element = atlas_thread_bottom
    return _get_atlas_prompt_send_button(closest_element)


def _get_atlas_prompt_send_button(starting_element: AXUIElementRef) -> AXUIElementRef | None:
    """Returns the Atlas prompt send button reference."""
    return find_live_first(starting_element, _is_atlas_prompt_send_button, maximum_depth=25)


def _is_atlas_prompt_send_button(element: AXUIElementRef) -> bool:
    """Returns True if the element is the Atlas prompt send button reference."""
    dom_identifier: Any | None = ax_get_attribute(element, "AXDOMIdentifier")
    description: Any | None = ax_get_attribute(element, "AXDescription")
    return str(dom_identifier) == "composer-submit-button" or str(description) in ["Send", "Send prompt"]


def get_atlas_prompt_stop_button(starting_element: AXUIElementRef) -> AXUIElementRef | None:
    """Returns the Atlas prompt stop button reference."""
    return find_live_first(starting_element, _is_atlas_prompt_stop_button, maximum_depth=25)


def _is_atlas_prompt_stop_button(element: AXUIElementRef) -> bool:
    """Returns True if the element is the Atlas prompt stop button reference."""
    description: Any | None = ax_get_attribute(element, "AXDescription")
    dom_identifier: AXUIElementRef | None = ax_get_attribute(element, "AXDOMIdentifier")
    if str(dom_identifier) == "composer-submit-button" or str(description) == "Stop streaming":
        logger.debug(f"{dom_identifier=}")
        logger.debug(f"{description=}")

    return str(description) == "Stop streaming" and str(dom_identifier) == "composer-submit-button"


def get_atlas_thread_bottom() -> AXUIElementRef | None:
    """Gets the Atlas reference that contains the text entry and submit button during extended prompts."""
    closest_element: AXUIElementRef = get_atlas_main_or_window()
    return _get_atlas_thread_bottom(closest_element)


def _get_atlas_thread_bottom(main_element: AXUIElementRef) -> AXUIElementRef | None:
    """Gets the Atlas reference that contains the text entry and submit button during extended prompts."""
    return find_live_first(main_element, _is_atlas_thread_bottom, maximum_depth=30)


def _is_atlas_thread_bottom(element: AXUIElementRef) -> bool:
    """Returns whether the provided element is the Atlas thread-bottom reference."""
    dom_identifier: Any = ax_get_attribute(element, "AXDOMIdentifier")
    return str(dom_identifier) == "thread-bottom"


def press_enter_in_atlas():
    """Press enter in Atlas.

    Overall avoid using this, only used for edge cases where AXPress / etc. won't work.
    """
    app_info: ApplicationInfo = get_or_create_atlas_application()

    key_down: Any = CGEventCreateKeyboardEvent(None, 36, True)
    key_up: Any = CGEventCreateKeyboardEvent(None, 36, False)

    CGEventPostToPid(app_info["process_id"], key_down)
    CGEventPostToPid(app_info["process_id"], key_up)


if __name__ == "__main__":
    while True:
        atlas_root: AXUIElementRef = get_atlas_ui()
        atlas_window: AXUIElementRef = _get_atlas_window(atlas_root)
        logger.info(get_atlas_prompt_stop_button(atlas_window))
