"""Hierarchy traversal and search functions.

This module provides functions for searching both:
- Cached hierarchies (AccessibilityElementDict) - fast, offline
- Live accessibility trees (AXUIElementRef) - current state, slower
"""

from __future__ import annotations

from typing import Any, Callable

from atlas.accessibility.constants import AXROLE_WEB_AREA
from atlas.accessibility.predicates import (
    create_role_predicate,
    create_subrole_predicate,
    create_title_predicate,
    create_identifier_predicate,
    create_value_predicate,
    create_attribute_predicate,
    create_live_role_predicate,
    create_live_title_predicate,
    create_live_identifier_predicate,
    has_url,
    is_interactive,
)
from atlas.accessibility.pure import element_hash
from atlas.accessibility._types import AccessibilityElementDict, AXUIElementRef, SearchResult


# =============================================================================
# HIERARCHY TRAVERSAL - Core Functions
# =============================================================================


def traverse_with_predicate(
    hierarchy: AccessibilityElementDict,
    predicate: Callable[[AccessibilityElementDict], bool],
    current_path: tuple[int, ...] = (),
    current_depth: int = 0,
) -> list[SearchResult]:
    """Traverse a hierarchy and collect elements matching a predicate.

    Uses immutable tuple for path tracking during recursion.

    Args:
        hierarchy: The hierarchy to traverse
        predicate: Function that returns True for matching elements
        current_path: Current path in the hierarchy (internal use)
        current_depth: Current depth level (internal use)

    Returns:
        List of SearchResult for all matching elements
    """
    results: list[SearchResult] = []

    if predicate(hierarchy):
        results.append(
            SearchResult(
                element=hierarchy,
                path=list(current_path),
                depth=current_depth,
            )
        )

    children: list[AccessibilityElementDict] = hierarchy.get("children", [])
    for child_index, child in enumerate(children):
        child_path: tuple[int, ...] = current_path + (child_index,)
        results.extend(traverse_with_predicate(child, predicate, child_path, current_depth + 1))

    windows: list[AccessibilityElementDict] = hierarchy.get("windows", [])
    for window_index, window in enumerate(windows):
        # Negative indices indicate windows
        window_path: tuple[int, ...] = current_path + (-(window_index + 1),)
        results.extend(traverse_with_predicate(window, predicate, window_path, current_depth + 1))

    return results


def find_by_predicate(
    hierarchy: AccessibilityElementDict,
    predicate: Callable[[AccessibilityElementDict], bool],
) -> list[SearchResult]:
    """Find all elements matching a predicate.

    Args:
        hierarchy: The hierarchy to search
        predicate: Function that returns True for matching elements

    Returns:
        List of SearchResult for all matching elements
    """
    return traverse_with_predicate(hierarchy, predicate)


def find_first_by_predicate(
    hierarchy: AccessibilityElementDict,
    predicate: Callable[[AccessibilityElementDict], bool],
) -> SearchResult | None:
    """Find the first element matching a predicate (depth-first).

    Args:
        hierarchy: The hierarchy to search
        predicate: Function that returns True for matching elements

    Returns:
        First matching SearchResult, or None if not found
    """
    results: list[SearchResult] = find_by_predicate(hierarchy, predicate)
    return results[0] if results else None


def extract_elements(results: list[SearchResult]) -> list[AccessibilityElementDict]:
    """Extract just the element dictionaries from search results.

    Args:
        results: List of SearchResult

    Returns:
        List of AccessibilityElementDict without path/depth info
    """
    return [result["element"] for result in results]


# =============================================================================
# PATH NAVIGATION
# =============================================================================


def navigate_to_path(
    hierarchy: AccessibilityElementDict,
    path: list[int],
) -> AccessibilityElementDict | None:
    """Navigate to an element at a specific path.

    Path indices work as follows:
    - Non-negative: Index into children list
    - Negative: Index into windows list (-(index + 1))

    Args:
        hierarchy: The root hierarchy
        path: List of indices forming the path

    Returns:
        The element at the path, or None if path is invalid
    """
    current: AccessibilityElementDict = hierarchy

    for index in path:
        if index < 0:
            window_index: int = -(index + 1)
            windows: list[AccessibilityElementDict] = current.get("windows", [])
            if window_index >= len(windows):
                return None
            current = windows[window_index]
        else:
            children: list[AccessibilityElementDict] = current.get("children", [])
            if index >= len(children):
                return None
            current = children[index]

    return current


# =============================================================================
# SPECIALIZED SEARCHES - By Attribute
# =============================================================================


def find_by_role(hierarchy: AccessibilityElementDict, role: str) -> list[AccessibilityElementDict]:
    """Find all elements with a specific role.

    Args:
        hierarchy: The hierarchy to search
        role: The AXRole to match (e.g., "AXButton")

    Returns:
        List of matching elements
    """
    return extract_elements(find_by_predicate(hierarchy, create_role_predicate(role)))


def find_by_subrole(hierarchy: AccessibilityElementDict, subrole: str) -> list[AccessibilityElementDict]:
    """Find all elements with a specific subrole.

    Args:
        hierarchy: The hierarchy to search
        subrole: The AXSubrole to match

    Returns:
        List of matching elements
    """
    return extract_elements(find_by_predicate(hierarchy, create_subrole_predicate(subrole)))


def find_by_title(
    hierarchy: AccessibilityElementDict,
    title: str,
    partial_match: bool = False,
    case_sensitive: bool = False,
) -> list[SearchResult]:
    """Find all elements with a specific title.

    Args:
        hierarchy: The hierarchy to search
        title: The title to match
        partial_match: If True, match if title contains the value
        case_sensitive: If False, ignore case

    Returns:
        List of SearchResult for matching elements
    """
    return find_by_predicate(hierarchy, create_title_predicate(title, partial_match, case_sensitive))


def find_by_identifier(
    hierarchy: AccessibilityElementDict,
    identifier: str,
    partial_match: bool = False,
) -> list[SearchResult]:
    """Find all elements with a specific identifier.

    Args:
        hierarchy: The hierarchy to search
        identifier: The AXIdentifier to match
        partial_match: If True, match if identifier contains the value

    Returns:
        List of SearchResult for matching elements
    """
    return find_by_predicate(hierarchy, create_identifier_predicate(identifier, partial_match))


def find_by_value(
    hierarchy: AccessibilityElementDict,
    value: str,
    partial_match: bool = True,
    case_sensitive: bool = False,
) -> list[SearchResult]:
    """Find all elements with a specific value.

    Args:
        hierarchy: The hierarchy to search
        value: The AXValue to match
        partial_match: If True, match if value contains the search term
        case_sensitive: If False, ignore case

    Returns:
        List of SearchResult for matching elements
    """
    return find_by_predicate(hierarchy, create_value_predicate(value, partial_match, case_sensitive))


def find_by_attribute(
    hierarchy: AccessibilityElementDict,
    attribute_name: str,
    attribute_value: str,
    partial_match: bool = False,
    case_sensitive: bool = True,
) -> list[SearchResult]:
    """Find all elements where an attribute matches a value.

    Args:
        hierarchy: The hierarchy to search
        attribute_name: Name of the attribute to match
        attribute_value: Value to match
        partial_match: If True, match if attribute contains the value
        case_sensitive: If False, ignore case

    Returns:
        List of SearchResult for matching elements
    """
    predicate: Callable[[AccessibilityElementDict], bool] = create_attribute_predicate(
        attribute_name, attribute_value, partial_match, case_sensitive
    )
    return find_by_predicate(hierarchy, predicate)


# =============================================================================
# SPECIALIZED SEARCHES - Web Content
# =============================================================================


def find_web_areas(hierarchy: AccessibilityElementDict) -> list[AccessibilityElementDict]:
    """Find all AXWebArea elements (web content containers).

    Args:
        hierarchy: The hierarchy to search

    Returns:
        List of web area elements
    """
    return find_by_role(hierarchy, AXROLE_WEB_AREA)


def find_innermost_web_area_with_title(hierarchy: AccessibilityElementDict) -> AccessibilityElementDict | None:
    """Find the innermost AXWebArea that has a title.

    In Chromium-based apps, web areas are often nested:
    AXWebArea > AXUnknown > AXWebArea (with title)

    This finds the deepest one with actual content.

    Args:
        hierarchy: The hierarchy to search

    Returns:
        The innermost web area with a title, or None
    """
    web_areas: list[AccessibilityElementDict] = find_web_areas(hierarchy)

    for web_area in reversed(web_areas):
        if web_area.get("AXTitle"):
            return web_area

    return web_areas[-1] if web_areas else None


def find_elements_with_url(hierarchy: AccessibilityElementDict) -> list[AccessibilityElementDict]:
    """Find all elements that have a URL attribute.

    Args:
        hierarchy: The hierarchy to search

    Returns:
        List of elements with AXURL attribute
    """
    return extract_elements(find_by_predicate(hierarchy, has_url))


# =============================================================================
# SPECIALIZED SEARCHES - Interactive Elements
# =============================================================================


def find_interactive_elements(hierarchy: AccessibilityElementDict) -> list[AccessibilityElementDict]:
    """Find all interactive elements (buttons, links, text fields, etc.).

    Args:
        hierarchy: The hierarchy to search

    Returns:
        List of interactive elements
    """
    return extract_elements(find_by_predicate(hierarchy, is_interactive))


def find_buttons(hierarchy: AccessibilityElementDict) -> list[AccessibilityElementDict]:
    """Find all button elements."""
    return find_by_role(hierarchy, "AXButton")


def find_links(hierarchy: AccessibilityElementDict) -> list[AccessibilityElementDict]:
    """Find all link elements."""
    return find_by_role(hierarchy, "AXLink")


def find_text_fields(hierarchy: AccessibilityElementDict) -> list[AccessibilityElementDict]:
    """Find all text field elements."""
    return find_by_role(hierarchy, "AXTextField")


def find_text_areas(hierarchy: AccessibilityElementDict) -> list[AccessibilityElementDict]:
    """Find all text area elements."""
    return find_by_role(hierarchy, "AXTextArea")


def find_static_text(hierarchy: AccessibilityElementDict) -> list[AccessibilityElementDict]:
    """Find all static text elements."""
    return find_by_role(hierarchy, "AXStaticText")


# =============================================================================
# LIVE HIERARCHY SEARCH
# =============================================================================


def find_live_by_predicate(
    starting_element: AXUIElementRef,
    predicate: Callable[[AXUIElementRef], bool],
    maximum_depth: int = 10,
    current_depth: int = 0,
    visited: frozenset[int] | None = None,
) -> AXUIElementRef | None:
    """Search the live accessibility hierarchy for an element.

    Unlike cached hierarchy searches, this queries the actual
    accessibility tree which reflects current application state.

    Args:
        starting_element: Element to start search from
        predicate: Function that returns True for matching elements
        maximum_depth: Maximum depth to traverse
        current_depth: Current depth (internal use)
        visited: Set of visited element hashes (internal use)

    Returns:
        First matching element, or None if not found
    """
    from atlas.accessibility.api import ax_get_attribute

    if visited is None:
        visited = frozenset()

    elem_hash: int = element_hash(starting_element)
    if elem_hash in visited or current_depth >= maximum_depth:
        return None

    if predicate(starting_element):
        return starting_element

    new_visited: frozenset[int] = visited | {elem_hash}
    children: Any | None = ax_get_attribute(starting_element, "AXChildren")

    if children:
        try:
            for i in range(len(children)):
                result: AXUIElementRef | None = find_live_by_predicate(
                    children[i], predicate, maximum_depth, current_depth + 1, new_visited
                )
                if result is not None:
                    return result
        except TypeError:
            pass

    return None


def find_live_by_role(
    starting_element: AXUIElementRef,
    role: str,
    maximum_depth: int = 10,
) -> AXUIElementRef | None:
    """Find the first element with a specific role in the live hierarchy.

    Args:
        starting_element: Element to start search from
        role: The AXRole to match
        maximum_depth: Maximum depth to traverse

    Returns:
        First matching element, or None if not found
    """
    return find_live_by_predicate(starting_element, create_live_role_predicate(role), maximum_depth)


def find_live_by_title(
    starting_element: AXUIElementRef,
    title: str,
    partial_match: bool = False,
    case_sensitive: bool = False,
    maximum_depth: int = 10,
) -> AXUIElementRef | None:
    """Find the first element with a specific title in the live hierarchy.

    Args:
        starting_element: Element to start search from
        title: The title to match
        partial_match: If True, match if title contains the value
        case_sensitive: If False, ignore case
        maximum_depth: Maximum depth to traverse

    Returns:
        First matching element, or None if not found
    """
    predicate: Callable[[AXUIElementRef], bool] = create_live_title_predicate(title, partial_match, case_sensitive)
    return find_live_by_predicate(starting_element, predicate, maximum_depth)


def find_live_by_identifier(
    starting_element: AXUIElementRef,
    identifier: str,
    maximum_depth: int = 10,
) -> AXUIElementRef | None:
    """Find the first element with a specific identifier in the live hierarchy.

    Args:
        starting_element: Element to start search from
        identifier: The AXIdentifier to match
        maximum_depth: Maximum depth to traverse

    Returns:
        First matching element, or None if not found
    """
    return find_live_by_predicate(starting_element, create_live_identifier_predicate(identifier), maximum_depth)


def find_live_web_area(
    starting_element: AXUIElementRef,
    maximum_depth: int = 10,
) -> AXUIElementRef | None:
    """Find the first AXWebArea element in the live hierarchy.

    Args:
        starting_element: Element to start search from
        maximum_depth: Maximum depth to traverse

    Returns:
        First web area element, or None if not found
    """
    return find_live_by_role(starting_element, AXROLE_WEB_AREA, maximum_depth)
