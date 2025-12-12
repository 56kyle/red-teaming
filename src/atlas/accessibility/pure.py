"""Pure utility functions with no side effects."""

from __future__ import annotations

import json
from typing import Any

from atlas.accessibility._types import AXUIElementRef
from atlas.accessibility._types import AccessibilityElementDict


# =============================================================================
# VALUE TRANSFORMATIONS
# =============================================================================


def coerce_to_string(value: Any) -> str:
    """Convert any value to a string representation.

    Args:
        value: Any value to convert

    Returns:
        String representation of the value

    Examples:
        >>> coerce_to_string(True)
        'true'
        >>> coerce_to_string([1, 2, 3])
        '1, 2, 3'
        >>> coerce_to_string("hello")
        'hello'
    """
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    return str(value)


def normalize_for_comparison(value: str, case_sensitive: bool) -> str:
    """Normalize a string for comparison.

    Args:
        value: String to normalize
        case_sensitive: Whether to preserve case

    Returns:
        Normalized string (lowercase if not case sensitive)
    """
    return value if case_sensitive else value.lower()


def element_hash(element: AXUIElementRef) -> int:
    """Generate a hash for an accessibility element.

    Used for cycle detection during hierarchy traversal.

    Args:
        element: The accessibility element to hash

    Returns:
        Integer hash value
    """
    return hash(element)


# =============================================================================
# JSON SERIALIZATION
# =============================================================================


def serialize_to_json(hierarchy: AccessibilityElementDict, indent: int = 2) -> str:
    """Serialize a hierarchy dictionary to a JSON string.

    Args:
        hierarchy: The hierarchy to serialize
        indent: Number of spaces for indentation

    Returns:
        Formatted JSON string
    """
    return json.dumps(hierarchy, indent=indent, default=str)


def deserialize_from_json(json_string: str) -> AccessibilityElementDict:
    """Deserialize a JSON string to a hierarchy dictionary.

    Args:
        json_string: JSON string to parse

    Returns:
        Parsed hierarchy dictionary
    """
    return json.loads(json_string)


# =============================================================================
# HIERARCHY STATISTICS
# =============================================================================


def count_elements_in_hierarchy(hierarchy: AccessibilityElementDict) -> int:
    """Count total elements in a hierarchy.

    Args:
        hierarchy: The hierarchy to count

    Returns:
        Total number of elements including nested children
    """
    count: int = 1  # Count self

    for child in hierarchy.get("children", []):
        count += count_elements_in_hierarchy(child)

    for window in hierarchy.get("windows", []):
        count += count_elements_in_hierarchy(window)

    return count


def get_hierarchy_depth(hierarchy: AccessibilityElementDict, current_depth: int = 0) -> int:
    """Calculate the maximum depth of a hierarchy.

    Args:
        hierarchy: The hierarchy to measure
        current_depth: Current depth (used internally for recursion)

    Returns:
        Maximum depth of the hierarchy
    """
    max_depth: int = current_depth

    for child in hierarchy.get("children", []):
        child_depth: int = get_hierarchy_depth(child, current_depth + 1)
        max_depth = max(max_depth, child_depth)

    for window in hierarchy.get("windows", []):
        window_depth: int = get_hierarchy_depth(window, current_depth + 1)
        max_depth = max(max_depth, window_depth)

    return max_depth


def collect_unique_roles(hierarchy: AccessibilityElementDict) -> set[str]:
    """Collect all unique roles present in a hierarchy.

    Args:
        hierarchy: The hierarchy to analyze

    Returns:
        Set of unique role strings
    """
    roles: set[str] = set()

    role: str | None = hierarchy.get("AXRole")
    if role:
        roles.add(role)

    for child in hierarchy.get("children", []):
        roles.update(collect_unique_roles(child))

    for window in hierarchy.get("windows", []):
        roles.update(collect_unique_roles(window))

    return roles
