"""Module containing logic for interacting with the Atlas user interface."""

from __future__ import annotations

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
except ImportError as import_error:
    logger.error(f"Failed to import required macOS frameworks: {import_error}")
    raise


def get_atlas_ui() -> AXUIElementRef:
    """Returns the live state of the atlas UI."""
    app_info: ApplicationInfo = get_or_create_atlas_application()
    atlas_root: AXUIElementRef = create_accessibility_element_for_application(app_info["process_id"])
    return atlas_root


def create_accessibility_element_for_application(process_id: int) -> AXUIElementRef:
    """Create an accessibility element reference for an application by process ID."""
    return AXUIElementCreateApplication(process_id)


def get_atlas_window(app_element: AXUIElementRef) -> AXUIElementRef | None:
    """Returns the first valid atlas window reference.

    For Chromium-based apps, AXFocusedWindow/AXMainWindow are more reliable
    than AXWindows. Windows from AXWindows are validated to have attributes.
    """
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

    return None


def get_atlas_web_areas(starting_element: AXUIElementRef, maximum_depth: int = 15) -> list[AXUIElementRef]:
    """Returns a list of atlas web areas references."""
    return find_live(starting_element, _is_atlas_web_area, maximum_depth=maximum_depth)


def _is_atlas_web_area(element: AXUIElementRef) -> bool:
    """Returns True if the element is the atlas web area."""
    result: AXUIElementRef = ax_get_attribute(element, "AXRole") == "AXWebArea"
    return result


def toggle_atlas_sidebar(starting_element: AXUIElementRef) -> None:
    """Opens the Atlas sidebar provided."""
    sidebar_button: AXUIElementRef = get_atlas_sidebar_button(starting_element)
    ax_perform_action(sidebar_button, "AXEnable")


def get_atlas_sidebar_button(starting_element: AXUIElementRef) -> AXUIElementRef:
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


def get_atlas_sidebar(starting_element: AXUIElementRef) -> AXUIElementRef | None:
    """Returns the Atlas sidebar reference."""
    return find_live_first(starting_element, _is_atlas_sidebar)


def _is_atlas_sidebar(element: AXUIElementRef) -> bool:
    """Returns True if the element is the Atlas sidebar."""
    title: str | None = ax_get_attribute(element, "AXTitle")
    subrole: str | None = ax_get_attribute(element, "AXSubrole")
    return str(title) == "Sidebar" and str(subrole) == "AXApplicationDialog"


def get_sidebar_conversation_links(sidebar_element: AXUIElementRef) -> list[AXUIElementRef]:
    """Returns a list of sidebar conversation link references."""
    navigation_element: AXUIElementRef = get_sidebar_navigation(sidebar_element)
    navigation_history_element: AXUIElementRef = get_sidebar_navigation_history(navigation_element)
    history_link_elements: list[AXUIElementRef] = find_all_navigation_history_links(navigation_history_element)
    return [ax_get_attribute(element, "AXURL") for element in history_link_elements]


def get_sidebar_navigation(sidebar_element: AXUIElementRef) -> AXUIElementRef | None:
    """Returns the Atlas sidebar navigation reference."""
    return find_live_first(sidebar_element, _is_sidebar_navigation)


def _is_sidebar_navigation(element: AXUIElementRef) -> bool:
    """Returns True if the element is the Atlas sidebar navigation reference."""
    subrole: str | None = ax_get_attribute(element, "AXSubrole")
    description: str | None = ax_get_attribute(element, "AXDescription")
    return subrole == "AXLandmarkNavigation" and description == "Chat history"


def get_sidebar_navigation_history(sidebar_navigation_element: AXUIElementRef) -> list[AXUIElementRef]:
    """Returns the Atlas sidebar navigation's history reference."""
    return find_live_first(sidebar_navigation_element, _is_sidebar_navigation)


def _is_sidebar_navigation_history(element: AXUIElementRef) -> bool:
    """Returns whether the given element is the Atlas sidebar navigation history reference."""
    dom_identifier: str | None = ax_get_attribute(element, "AXDOMIdentifier")
    return dom_identifier == "history"


def find_all_navigation_history_links(navigation_history_element: AXUIElementRef) -> list[AXUIElementRef]:
    """Returns all Atlas sidebar history navigation link references."""
    return find_live(navigation_history_element, _is_navigation_history_link)


def _is_navigation_history_link(element: AXUIElementRef) -> bool:
    """Returns True if the element is an Atlas sidebar's navigation history link."""
    role: str | None = ax_get_attribute(element, "AXRole")
    url: str | None = ax_get_attribute(element, "AXURL")
    return role == "AXLink" and str(url).startswith("https://chatgpt.com/c/")


if __name__ == "__main__":
    atlas_root: AXUIElementRef = get_atlas_ui()
    atlas_window: AXUIElementRef = get_atlas_window(atlas_root)
    sidebar: AXUIElementRef = get_atlas_sidebar(atlas_window)
    links: list[str] = get_sidebar_conversation_links(sidebar)
    logger.info(links)

