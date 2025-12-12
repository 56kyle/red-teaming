"""Hierarchy conversion functions.

This module handles converting live accessibility elements (AXUIElementRef)
into dictionary representations (AccessibilityElementDict).
"""

from __future__ import annotations

from typing import Any

from atlas.accessibility import ax_get_element_at_position
from atlas.accessibility._types import AXUIElementRef
from atlas.accessibility._types import AccessibilityElementDict
from atlas.accessibility._types import ConversionConfig
from atlas.accessibility._types import PointDict
from atlas.accessibility._types import SizeDict
from atlas.accessibility.api import ax_create_application_element
from atlas.accessibility.api import ax_create_system_wide_element
from atlas.accessibility.api import ax_extract_point
from atlas.accessibility.api import ax_extract_size
from atlas.accessibility.api import ax_get_attribute
from atlas.accessibility.api import ax_get_attribute_names
from atlas.accessibility.api import ax_get_parameterized_attribute_names
from atlas.accessibility.api import ax_get_valid_windows
from atlas.accessibility.pure import coerce_to_string
from atlas.accessibility.pure import element_hash


def convert_element(
    element: AXUIElementRef,
    config: ConversionConfig,
    current_depth: int = 0,
    visited: frozenset[int] | None = None,
) -> AccessibilityElementDict:
    """Convert an accessibility element to a dictionary representation.

    Recursively converts the element and all its children, handling
    cycle detection and depth limits.

    Args:
        element: The accessibility element to convert
        config: Conversion configuration
        current_depth: Current depth in hierarchy (internal use)
        visited: Set of visited element hashes (internal use)

    Returns:
        Dictionary representation of the element
    """
    if visited is None:
        visited = frozenset()

    elem_hash: int = element_hash(element)

    if elem_hash in visited:
        return AccessibilityElementDict(cycle_detected=True)

    if current_depth >= config.maximum_depth:
        return AccessibilityElementDict(truncated=True)

    new_visited: frozenset[int] = visited | {elem_hash}
    result: AccessibilityElementDict = {}

    # Include available attributes if requested
    if config.include_available_attributes:
        result["available_attributes"] = ax_get_attribute_names(element)

    # Include parameterized attributes if requested
    if config.include_parameterized_attributes:
        param_attrs: list[str] = ax_get_parameterized_attribute_names(element)
        if param_attrs:
            result["available_parameterized_attributes"] = param_attrs

    # Capture requested attributes
    for attr_name in config.attributes_to_capture:
        value: Any | None = ax_get_attribute(element, attr_name)
        if value is not None:
            result[attr_name] = coerce_to_string(value)

    # Extract position
    position_ref: Any | None = ax_get_attribute(element, "AXPosition")
    if position_ref is not None:
        position: PointDict | None = ax_extract_point(position_ref)
        if position is not None:
            result["position"] = position

    # Extract size
    size_ref: Any | None = ax_get_attribute(element, "AXSize")
    if size_ref is not None:
        size: SizeDict | None = ax_extract_size(size_ref)
        if size is not None:
            result["size"] = size

    # Convert children recursively
    children: Any | None = ax_get_attribute(element, "AXChildren")
    if children and len(children) > 0:
        result["children"] = [
            convert_element(children[i], config, current_depth + 1, new_visited)
            for i in range(len(children))
        ]

    return result


def convert_application(
    process_id: int,
    config: ConversionConfig = ConversionConfig(),
) -> AccessibilityElementDict:
    """Convert an application's accessibility hierarchy to a dictionary.

    Handles window retrieval properly for both standard apps and
    Chromium-based apps (which require special handling).

    Args:
        process_id: The application's process ID
        config: Conversion configuration

    Returns:
        Dictionary representation of the application hierarchy
    """
    app_element: AXUIElementRef = ax_create_application_element(process_id)

    # Convert the application element itself
    result: AccessibilityElementDict = convert_element(app_element, config)

    # Get and convert windows
    windows: list[AXUIElementRef] = ax_get_valid_windows(app_element)

    if windows:
        window_dicts: list[AccessibilityElementDict] = [
            convert_element(window, config, current_depth=1)
            for window in windows
        ]

        if config.include_windows_as_children:
            existing_children: list[AccessibilityElementDict] = result.get("children", [])
            result["children"] = existing_children + window_dicts
        else:
            result["windows"] = window_dicts

    return result


def convert_focused_element(config: ConversionConfig = ConversionConfig()) -> AccessibilityElementDict | None:
    """Convert the currently focused element to a dictionary.

    Args:
        config: Conversion configuration

    Returns:
        Dictionary representation of the focused element, or None
    """
    system_wide: AXUIElementRef = ax_create_system_wide_element()
    focused: Any | None = ax_get_attribute(system_wide, "AXFocusedUIElement")

    if focused is not None:
        return convert_element(focused, config)
    return None


def convert_element_at_position(
    x: float,
    y: float,
    config: ConversionConfig = ConversionConfig(),
) -> AccessibilityElementDict | None:
    """Convert the element at a screen position to a dictionary.

    Args:
        x: Screen X coordinate
        y: Screen Y coordinate
        config: Conversion configuration

    Returns:
        Dictionary representation of the element, or None if not found
    """
    element: AXUIElementRef | None = ax_get_element_at_position(x, y)
    if element is not None:
        return convert_element(element, config)
    return None
