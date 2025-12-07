"""Predicate factory functions for element matching.

This module provides factory functions that create predicate functions
for matching accessibility elements based on various criteria.

Two types of predicates are provided:
- Dict predicates: Work on AccessibilityElementDict (cached hierarchies)
- Live predicates: Work on AXUIElementRef (live accessibility tree)
"""

from __future__ import annotations

from typing import Any, Callable

from atlas.accessibility.api import ax_get_attribute
from atlas.accessibility.constants import INTERACTIVE_ROLES, AXROLE_WEB_AREA
from atlas.accessibility.pure import normalize_for_comparison
from atlas.accessibility._types import AccessibilityElementDict, AXUIElementRef


# =============================================================================
# DICT PREDICATES - For AccessibilityElementDict
# =============================================================================


def create_attribute_predicate(
    attribute_name: str,
    attribute_value: str,
    partial_match: bool = False,
    case_sensitive: bool = True,
) -> Callable[[AccessibilityElementDict], bool]:
    """Create a predicate that matches elements by attribute value.

    Args:
        attribute_name: Name of the attribute to match
        attribute_value: Value to match against
        partial_match: If True, check if value is contained in attribute
        case_sensitive: If False, perform case-insensitive comparison

    Returns:
        A predicate function that takes an element dict and returns bool

    Example:
        >>> pred = create_attribute_predicate("AXRole", "AXButton")
        >>> pred({"AXRole": "AXButton"})
        True
    """
    normalized_search: str = normalize_for_comparison(attribute_value, case_sensitive)

    def predicate(element: AccessibilityElementDict) -> bool:
        element_value: str | None = element.get(attribute_name)
        if element_value is None:
            return False

        normalized_element: str = normalize_for_comparison(element_value, case_sensitive)

        if partial_match:
            return normalized_search in normalized_element
        return normalized_element == normalized_search

    return predicate


def create_role_predicate(role: str) -> Callable[[AccessibilityElementDict], bool]:
    """Create a predicate that matches elements by role.

    Args:
        role: The AXRole value to match (e.g., "AXButton")

    Returns:
        A predicate function
    """
    return create_attribute_predicate("AXRole", role)


def create_subrole_predicate(subrole: str) -> Callable[[AccessibilityElementDict], bool]:
    """Create a predicate that matches elements by subrole.

    Args:
        subrole: The AXSubrole value to match

    Returns:
        A predicate function
    """
    return create_attribute_predicate("AXSubrole", subrole)


def create_title_predicate(
    title: str,
    partial_match: bool = False,
    case_sensitive: bool = False,
) -> Callable[[AccessibilityElementDict], bool]:
    """Create a predicate that matches elements by title.

    Args:
        title: The title to match
        partial_match: If True, match if title contains the value
        case_sensitive: If False, ignore case

    Returns:
        A predicate function
    """
    return create_attribute_predicate("AXTitle", title, partial_match, case_sensitive)


def create_identifier_predicate(
    identifier: str,
    partial_match: bool = False,
) -> Callable[[AccessibilityElementDict], bool]:
    """Create a predicate that matches elements by identifier.

    Args:
        identifier: The AXIdentifier to match
        partial_match: If True, match if identifier contains the value

    Returns:
        A predicate function
    """
    return create_attribute_predicate("AXIdentifier", identifier, partial_match, case_sensitive=True)


def create_value_predicate(
    value: str,
    partial_match: bool = True,
    case_sensitive: bool = False,
) -> Callable[[AccessibilityElementDict], bool]:
    """Create a predicate that matches elements by value.

    Args:
        value: The AXValue to match
        partial_match: If True, match if value contains the search term
        case_sensitive: If False, ignore case

    Returns:
        A predicate function
    """
    return create_attribute_predicate("AXValue", value, partial_match, case_sensitive)


def create_role_and_title_predicate(
    role: str,
    title: str,
    partial_title_match: bool = False,
) -> Callable[[AccessibilityElementDict], bool]:
    """Create a predicate that matches elements by both role and title.

    Args:
        role: The AXRole to match
        title: The title to match
        partial_title_match: If True, match if title contains the value

    Returns:
        A predicate function
    """
    role_pred: Callable[[AccessibilityElementDict], bool] = create_role_predicate(role)
    title_pred: Callable[[AccessibilityElementDict], bool] = create_title_predicate(title, partial_title_match)

    def predicate(element: AccessibilityElementDict) -> bool:
        return role_pred(element) and title_pred(element)

    return predicate


# =============================================================================
# BUILT-IN PREDICATES - For AccessibilityElementDict
# =============================================================================


def has_url(element: AccessibilityElementDict) -> bool:
    """Predicate that checks if an element has a URL attribute."""
    return element.get("AXURL") is not None


def is_interactive(element: AccessibilityElementDict) -> bool:
    """Predicate that checks if an element is interactive."""
    return element.get("AXRole") in INTERACTIVE_ROLES


def is_web_area(element: AccessibilityElementDict) -> bool:
    """Predicate that checks if an element is a web area."""
    return element.get("AXRole") == AXROLE_WEB_AREA


def is_enabled(element: AccessibilityElementDict) -> bool:
    """Predicate that checks if an element is enabled."""
    return element.get("AXEnabled") == "true"


def is_focused(element: AccessibilityElementDict) -> bool:
    """Predicate that checks if an element is focused."""
    return element.get("AXFocused") == "true"


def has_children(element: AccessibilityElementDict) -> bool:
    """Predicate that checks if an element has children."""
    children: list[AccessibilityElementDict] = element.get("children", [])
    return len(children) > 0


def has_title(element: AccessibilityElementDict) -> bool:
    """Predicate that checks if an element has a non-empty title."""
    title: str | None = element.get("AXTitle")
    return title is not None and len(title) > 0


def has_value(element: AccessibilityElementDict) -> bool:
    """Predicate that checks if an element has a non-empty value."""
    value: str | None = element.get("AXValue")
    return value is not None and len(value) > 0


# =============================================================================
# LIVE PREDICATES - For AXUIElementRef
# =============================================================================


def create_live_role_predicate(target_role: str) -> Callable[[AXUIElementRef], bool]:
    """Create a predicate for live element role matching.

    Note: This imports ax_get_attribute at call time to avoid circular imports.

    Args:
        target_role: The role to match

    Returns:
        A predicate function for live elements
    """

    def predicate(element: AXUIElementRef) -> bool:
        role: Any | None = ax_get_attribute(element, "AXRole")
        return role == target_role

    return predicate


def create_live_subrole_predicate(target_subrole: str) -> Callable[[AXUIElementRef], bool]:
    """Create a predicate for live element subrole matching.

    Note: This imports ax_get_attribute at call time to avoid circular imports.

    Args:
        target_subrole: The subrole to match

    Returns:
        A predicate function for live elements
    """

    def predicate(element: AXUIElementRef) -> bool:
        subrole: Any | None = ax_get_attribute(element, "AXSubrole")
        return subrole == target_subrole

    return predicate


def create_live_title_predicate(
    target_title: str,
    partial_match: bool = False,
    case_sensitive: bool = False,
) -> Callable[[AXUIElementRef], bool]:
    """Create a predicate for live element title matching.

    Args:
        target_title: The title to match
        partial_match: If True, match if title contains the value
        case_sensitive: If False, ignore case

    Returns:
        A predicate function for live elements
    """
    normalized_target: str = normalize_for_comparison(target_title, case_sensitive)

    def predicate(element: AXUIElementRef) -> bool:
        title: Any | None = ax_get_attribute(element, "AXTitle")
        if title is None:
            return False

        normalized_title: str = normalize_for_comparison(str(title), case_sensitive)

        if partial_match:
            return normalized_target in normalized_title
        return normalized_title == normalized_target

    return predicate


def create_live_identifier_predicate(target_identifier: str) -> Callable[[AXUIElementRef], bool]:
    """Create a predicate for live element identifier matching.

    Args:
        target_identifier: The identifier to match

    Returns:
        A predicate function for live elements
    """

    def predicate(element: AXUIElementRef) -> bool:
        identifier: Any | None = ax_get_attribute(element, "AXIdentifier")
        return identifier == target_identifier

    return predicate


def create_live_value_predicate(
    target_value: str,
    partial_match: bool = True,
    case_sensitive: bool = False,
) -> Callable[[AXUIElementRef], bool]:
    """Create a predicate for live element value matching.

    Args:
        target_value: The value to match
        partial_match: If True, match if value contains the search term
        case_sensitive: If False, ignore case

    Returns:
        A predicate function for live elements
    """
    normalized_target: str = normalize_for_comparison(target_value, case_sensitive)

    def predicate(element: AXUIElementRef) -> bool:
        value: Any | None = ax_get_attribute(element, "AXValue")
        if value is None:
            return False

        normalized_value: str = normalize_for_comparison(str(value), case_sensitive)

        if partial_match:
            return normalized_target in normalized_value
        return normalized_value == normalized_target

    return predicate


# =============================================================================
# PREDICATE COMBINATORS
# =============================================================================


def combine_predicates_and(
    *predicates: Callable[[AccessibilityElementDict], bool],
) -> Callable[[AccessibilityElementDict], bool]:
    """Combine predicates with AND logic.

    Args:
        *predicates: Variable number of predicates to combine

    Returns:
        A predicate that returns True only if all predicates return True
    """

    def combined(element: AccessibilityElementDict) -> bool:
        return all(pred(element) for pred in predicates)

    return combined


def combine_predicates_or(
    *predicates: Callable[[AccessibilityElementDict], bool],
) -> Callable[[AccessibilityElementDict], bool]:
    """Combine predicates with OR logic.

    Args:
        *predicates: Variable number of predicates to combine

    Returns:
        A predicate that returns True if any predicate returns True
    """

    def combined(element: AccessibilityElementDict) -> bool:
        return any(pred(element) for pred in predicates)

    return combined


def negate_predicate(
    predicate: Callable[[AccessibilityElementDict], bool],
) -> Callable[[AccessibilityElementDict], bool]:
    """Negate a predicate.

    Args:
        predicate: The predicate to negate

    Returns:
        A predicate that returns the opposite of the input predicate
    """

    def negated(element: AccessibilityElementDict) -> bool:
        return not predicate(element)

    return negated
