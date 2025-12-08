"""Module containing logic for interacting with the Atlas user interface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict
from typing import TypeAlias

from loguru import logger

from atlas.accessibility import ax_get_attribute_names
from atlas.accessibility import find_live
from atlas.accessibility import find_live_by_subrole
from atlas.accessibility import find_live_innermost_web_area_with_title
from atlas.accessibility.api import ax_get_children
from atlas.accessibility.predicates import create_live_subrole_predicate
from atlas.hierarchy_broad import find_web_area_elements_in_hierarchy
from atlas.search_dynamic_functional import ax_get_attribute


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


AXUIElementRef: TypeAlias = Any


class ApplicationInfo(TypedDict):
    """Represents a running application's info."""
    name: str
    process_id: int
    bundle_identifier: str | None


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


def get_atlas_ui() -> AXUIElementRef:
    """Returns the live state of the atlas UI."""
    app_info: ApplicationInfo | None = find_application_info_by_name_substring("atlas")
    if app_info is None:
        raise RuntimeError("Failed to find a running instance of atlas.")
    atlas_root: AXUIElementRef = create_accessibility_element_for_application(app_info["process_id"])
    return atlas_root


def find_application_info_by_name_substring(
    name_substring: str,
    case_sensitive: bool = False,
) -> ApplicationInfo | None:
    """Find a running application whose name contains the given substring."""
    running_applications: list[ApplicationInfo] = get_running_applications_with_regular_activation_policy()

    normalized_search_substring: str = name_substring if case_sensitive else name_substring.lower()

    for application_info in running_applications:
        application_name: str = application_info["name"]
        normalized_application_name: str = application_name if case_sensitive else application_name.lower()

        if normalized_search_substring in normalized_application_name:
            return application_info

    return None


def get_running_applications_with_regular_activation_policy() -> list[ApplicationInfo]:
    """Retrieve all running applications that have a regular activation policy."""
    shared_workspace: Any = NSWorkspace.sharedWorkspace()
    running_applications: Any = shared_workspace.runningApplications()

    application_info_list: list[ApplicationInfo] = []

    for application in running_applications:
        activation_policy: int = application.activationPolicy()

        if activation_policy == NSApplicationActivationPolicyRegular:
            application_info: ApplicationInfo = {
                "name": application.localizedName(),
                "process_id": application.processIdentifier(),
                "bundle_identifier": application.bundleIdentifier(),
            }
            application_info_list.append(application_info)

    return application_info_list


def create_accessibility_element_for_application(process_id: int) -> AXUIElementRef:
    """Create an accessibility element reference for an application by process ID."""
    return AXUIElementCreateApplication(process_id)
