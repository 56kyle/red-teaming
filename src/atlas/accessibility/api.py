"""macOS Accessibility API wrappers.

This module provides thin wrappers around the macOS Accessibility API functions.
All functions are prefixed with 'ax_' to indicate they interact with the system.

These functions perform system calls but are otherwise deterministic.
"""

from __future__ import annotations

from typing import Any
from typing import Iterable
from typing import Optional

from loguru import logger

from atlas.accessibility._types import AXUIElementRef
from atlas.accessibility._types import ApplicationInfo
from atlas.accessibility._types import BoundsDict
from atlas.accessibility._types import PointDict
from atlas.accessibility._types import RangeDict
from atlas.accessibility._types import SizeDict


try:
    from ApplicationServices import (
        AXUIElementCopyAttributeValue,
        AXUIElementCopyAttributeValues,
        AXUIElementCopyAttributeNames,
        AXUIElementCopyParameterizedAttributeValue,
        AXUIElementCopyParameterizedAttributeNames,
        AXUIElementCopyActionNames,
        AXUIElementPerformAction,
        AXUIElementSetAttributeValue,
        AXUIElementCreateApplication,
        AXUIElementCreateSystemWide,
        kAXChildrenAttribute,
        AXValueGetValue,
        kAXValueTypeCGPoint,
        kAXValueTypeCGSize,
        kAXValueTypeCFRange,
        kAXErrorSuccess,
        kAXErrorActionUnsupported,
        kAXErrorAttributeUnsupported,
        kAXErrorInvalidUIElement,
        kAXErrorCannotComplete,
        kAXErrorNotImplemented,
    )
    from Cocoa import (
        NSApplicationActivationPolicyRegular,
        NSWorkspace,
    )
    from CoreFoundation import CFRange
    from Quartz import CGPoint
except ImportError as import_error:
    logger.error(f"Failed to import required macOS frameworks: {import_error}")
    raise


# =============================================================================
# ERROR CODE MAPPING
# =============================================================================

AX_ERROR_NAMES: dict[int, str] = {
    0: "kAXErrorSuccess",
    -25200: "kAXErrorFailure",
    -25201: "kAXErrorIllegalArgument",
    -25202: "kAXErrorInvalidUIElement",
    -25203: "kAXErrorInvalidUIElementObserver",
    -25204: "kAXErrorCannotComplete",
    -25205: "kAXErrorAttributeUnsupported",
    -25206: "kAXErrorActionUnsupported",
    -25207: "kAXErrorNotificationUnsupported",
    -25208: "kAXErrorNotImplemented",
    -25209: "kAXErrorNotificationAlreadyRegistered",
    -25210: "kAXErrorNotificationNotRegistered",
    -25211: "kAXErrorAPIDisabled",
    -25212: "kAXErrorNoValue",
    -25213: "kAXErrorParameterizedAttributeUnsupported",
    -25214: "kAXErrorNotEnoughPrecision",
}


# =============================================================================
# CORE ATTRIBUTE ACCESS
# =============================================================================


def ax_get_attribute(element: AXUIElementRef, attribute_name: str) -> Any | None:
    """Get an attribute value from an accessibility element.

    Args:
        element: The accessibility element to query
        attribute_name: Name of the attribute (e.g., "AXRole", "AXTitle")

    Returns:
        The attribute value, or None if not available
    """
    error_code: int
    value: Any
    error_code, value = AXUIElementCopyAttributeValue(element, attribute_name, None)
    return value if error_code == 0 else None


def ax_get_values(element: Any, attribute: str) -> Optional[list[Any]]:
    """Return an AX attribute's values or None."""
    try:
        status: int
        result: Iterable[Any]
        status, result = AXUIElementCopyAttributeValues(element, attribute, 0, 100, None)
        return result if status == 0 else None
    except Exception as e:
        logger.warning(e)
        return None


def ax_get_attribute_names(element: AXUIElementRef) -> list[str]:
    """Get all attribute names for an accessibility element.

    Args:
        element: The accessibility element to query

    Returns:
        List of attribute names, or empty list if unavailable
    """
    error_code: int
    names: Any
    error_code, names = AXUIElementCopyAttributeNames(element, None)
    return list(names) if error_code == 0 else []


def ax_get_children(element: Any) -> list[Any]:
    """Return a list of an AX element's children."""
    raw_children: Optional[Any] = ax_get_values(element, kAXChildrenAttribute)
    return list(raw_children) if raw_children is not None else []


def ax_get_parameterized_attribute_names(element: AXUIElementRef) -> list[str]:
    """Get all parameterized attribute names for an accessibility element.

    Args:
        element: The accessibility element to query

    Returns:
        List of parameterized attribute names
    """
    error_code: int
    names: Any
    error_code, names = AXUIElementCopyParameterizedAttributeNames(element, None)
    return list(names) if error_code == 0 else []


def ax_get_parameterized_attribute(
    element: AXUIElementRef,
    attribute_name: str,
    parameter: Any,
) -> Any | None:
    """Get a parameterized attribute value from an accessibility element.

    Common parameterized attributes:
    - AXStringForRange: Get string for a CFRange -> str
    - AXAttributedStringForRange: Get attributed string for CFRange
    - AXBoundsForRange: Get screen bounds for CFRange -> CGRect
    - AXRangeForLine: Get CFRange for line number
    - AXLineForIndex: Get line number for character index -> int
    - AXRangeForIndex: Get word/character range at index
    - AXRangeForPosition: Get text range at screen position
    - AXCellForColumnAndRow: Get table cell at column/row

    Args:
        element: The accessibility element to query
        attribute_name: Name of the parameterized attribute
        parameter: The parameter value (type depends on attribute)

    Returns:
        The attribute value, or None if not available
    """
    error_code: int
    value: Any
    error_code, value = AXUIElementCopyParameterizedAttributeValue(
        element, attribute_name, parameter, None
    )
    return value if error_code == 0 else None


# =============================================================================
# ELEMENT CREATION
# =============================================================================


def ax_create_application_element(process_id: int) -> AXUIElementRef:
    """Create an accessibility element for an application.

    Args:
        process_id: The process ID (PID) of the application

    Returns:
        An accessibility element reference for the application
    """
    return AXUIElementCreateApplication(process_id)


def ax_create_system_wide_element() -> AXUIElementRef:
    """Create a system-wide accessibility element.

    Returns:
        An accessibility element reference for system-wide operations
    """
    return AXUIElementCreateSystemWide()


# =============================================================================
# VALUE EXTRACTION
# =============================================================================


def ax_extract_point(value_reference: Any) -> PointDict | None:
    """Extract a point from an AXValue reference.

    Args:
        value_reference: An AXValue containing a CGPoint

    Returns:
        A PointDict with x and y, or None if extraction fails
    """
    succeeded: bool
    point: Any
    succeeded, point = AXValueGetValue(value_reference, kAXValueTypeCGPoint, None)
    return PointDict(x=point.x, y=point.y) if succeeded else None


def ax_extract_size(value_reference: Any) -> SizeDict | None:
    """Extract a size from an AXValue reference.

    Args:
        value_reference: An AXValue containing a CGSize

    Returns:
        A SizeDict with width and height, or None if extraction fails
    """
    succeeded: bool
    size: Any
    succeeded, size = AXValueGetValue(value_reference, kAXValueTypeCGSize, None)
    return SizeDict(width=size.width, height=size.height) if succeeded else None


def ax_extract_range(value_reference: Any) -> RangeDict | None:
    """Extract a range from an AXValue reference.

    Args:
        value_reference: An AXValue containing a CFRange

    Returns:
        A RangeDict with location and length, or None if extraction fails
    """
    succeeded: bool
    range_value: Any
    succeeded, range_value = AXValueGetValue(value_reference, kAXValueTypeCFRange, None)
    return RangeDict(location=range_value.location, length=range_value.length) if succeeded else None


# =============================================================================
# PARAMETER CREATION
# =============================================================================


def ax_create_cfrange(location: int, length: int) -> CFRange:
    """Create a CFRange for use with parameterized attributes.

    Args:
        location: Starting index
        length: Number of elements

    Returns:
        A CFRange object
    """
    return CFRange(location, length)


def ax_create_cgpoint(x: float, y: float) -> CGPoint:
    """Create a CGPoint for use with parameterized attributes.

    Args:
        x: X coordinate
        y: Y coordinate

    Returns:
        A CGPoint object
    """
    return CGPoint(x, y)


# =============================================================================
# TEXT ELEMENT HELPERS
# =============================================================================


def ax_get_string_for_range(element: AXUIElementRef, location: int, length: int) -> str | None:
    """Get the string within a range from a text element.

    Args:
        element: A text element (AXTextArea, AXTextField, etc.)
        location: Starting character index
        length: Number of characters

    Returns:
        The string within the range, or None if unavailable
    """
    result: Any | None = ax_get_parameterized_attribute(
        element, "AXStringForRange", ax_create_cfrange(location, length)
    )
    return str(result) if result is not None else None


def ax_get_line_for_index(element: AXUIElementRef, index: int) -> int | None:
    """Get the line number for a character index.

    Args:
        element: A text element
        index: Character index

    Returns:
        The line number, or None if unavailable
    """
    result: Any | None = ax_get_parameterized_attribute(element, "AXLineForIndex", index)
    return int(result) if result is not None else None


def ax_get_range_for_line(element: AXUIElementRef, line_number: int) -> RangeDict | None:
    """Get the character range for a line.

    Args:
        element: A text element
        line_number: Zero-based line number

    Returns:
        The character range for the line, or None if unavailable
    """
    result: Any | None = ax_get_parameterized_attribute(element, "AXRangeForLine", line_number)
    return ax_extract_range(result) if result is not None else None


def ax_get_bounds_for_range(element: AXUIElementRef, location: int, length: int) -> BoundsDict | None:
    """Get the screen bounds for a text range.

    Args:
        element: A text element
        location: Starting character index
        length: Number of characters

    Returns:
        The screen bounds (position and size), or None if unavailable
    """
    result: Any | None = ax_get_parameterized_attribute(
        element, "AXBoundsForRange", ax_create_cfrange(location, length)
    )
    if result is not None:
        try:
            return BoundsDict(
                position=PointDict(x=result.origin.x, y=result.origin.y),
                size=SizeDict(width=result.size.width, height=result.size.height),
            )
        except AttributeError:
            pass
    return None


def ax_get_range_for_position(element: AXUIElementRef, x: float, y: float) -> RangeDict | None:
    """Get the text range at a screen position.

    Args:
        element: A text element
        x: Screen X coordinate
        y: Screen Y coordinate

    Returns:
        The text range at that position, or None if unavailable
    """
    result: Any | None = ax_get_parameterized_attribute(
        element, "AXRangeForPosition", ax_create_cgpoint(x, y)
    )
    return ax_extract_range(result) if result is not None else None


def ax_get_cell_at_position(element: AXUIElementRef, column: int, row: int) -> AXUIElementRef | None:
    """Get a table cell at a specific position.

    Args:
        element: A table element
        column: Column index
        row: Row index

    Returns:
        The cell element, or None if unavailable
    """
    return ax_get_parameterized_attribute(element, "AXCellForColumnAndRow", [column, row])


def ax_get_element_at_position(
    x: float,
    y: float,
    starting_element: AXUIElementRef | None = None,
) -> AXUIElementRef | None:
    """Get the accessibility element at a screen position.

    Performs a hit test to find the deepest element at the given coordinates.

    Args:
        x: Screen X coordinate
        y: Screen Y coordinate
        starting_element: Element to start from (defaults to system-wide)

    Returns:
        The element at that position, or None if not found
    """
    if starting_element is None:
        starting_element = ax_create_system_wide_element()

    try:
        from ApplicationServices import AXUIElementCopyElementAtPosition
        error_code: int
        element: Any
        error_code, element = AXUIElementCopyElementAtPosition(starting_element, x, y, None)
        return element if error_code == 0 else None
    except ImportError:
        return None


# =============================================================================
# APPLICATION MANAGEMENT
# =============================================================================


def ax_get_running_applications() -> list[ApplicationInfo]:
    """Get all running applications with regular activation policy.

    Regular activation policy indicates standard GUI applications
    that appear in the Dock and can be activated by the user.

    Returns:
        List of ApplicationInfo dictionaries
    """
    workspace: Any = NSWorkspace.sharedWorkspace()
    apps: Any = workspace.runningApplications()

    return [
        ApplicationInfo(
            name=app.localizedName(),
            process_id=app.processIdentifier(),
            bundle_identifier=app.bundleIdentifier(),
        )
        for app in apps
        if app.activationPolicy() == NSApplicationActivationPolicyRegular
    ]


def ax_get_valid_windows(application_element: AXUIElementRef) -> list[AXUIElementRef]:
    """Get valid window elements from an application element.

    Handles Chromium-based apps which often return empty AXWindows,
    by falling back to AXFocusedWindow and AXMainWindow.

    Args:
        application_element: The application's accessibility element

    Returns:
        List of valid window elements
    """
    # Try focused/main window first (more reliable for Chromium-based apps)
    for attr in ("AXFocusedWindow", "AXMainWindow"):
        window: Any | None = ax_get_attribute(application_element, attr)
        if window is not None:
            if len(ax_get_attribute_names(window)) > 0:
                return [window]

    # Fall back to AXWindows array
    windows: Any | None = ax_get_attribute(application_element, "AXWindows")
    if windows is not None:
        try:
            valid: list[AXUIElementRef] = [
                windows[i] for i in range(len(windows))
                if len(ax_get_attribute_names(windows[i])) > 0
            ]
            if valid:
                return valid
        except TypeError:
            pass

    return []


def ax_get_focused_element() -> AXUIElementRef | None:
    """Get the currently focused accessibility element system-wide.

    Returns:
        The focused element, or None if not available
    """
    system_wide: AXUIElementRef = ax_create_system_wide_element()
    return ax_get_attribute(system_wide, "AXFocusedUIElement")


# =============================================================================
# UI INTERACTION
# =============================================================================


def ax_get_action_names(element: AXUIElementRef) -> list[str]:
    """Get all available action names for an accessibility element.

    Common actions include:
    - AXPress: Click/activate the element
    - AXIncrement/AXDecrement: For sliders, steppers
    - AXConfirm/AXCancel: For dialogs
    - AXShowMenu: Show context menu
    - AXPick: Select an item
    - AXRaise: Bring window to front

    Args:
        element: The accessibility element to query

    Returns:
        List of action names, or empty list if unavailable
    """
    error_code: int
    names: Any
    error_code, names = AXUIElementCopyActionNames(element, None)
    return list(names) if error_code == 0 else []


def ax_perform_action(element: AXUIElementRef, action_name: str) -> bool:
    """Perform an action on an accessibility element.

    Args:
        element: The accessibility element to act on
        action_name: Name of the action (e.g., "AXPress", "AXShowMenu")

    Returns:
        True if the action was performed successfully, False otherwise
    """
    error_code: int = AXUIElementPerformAction(element, action_name)
    if error_code != 0:
        error_name: str = AX_ERROR_NAMES.get(error_code, f"Unknown error {error_code}")
        logger.debug(f"ax_perform_action failed: {error_name}")
    return error_code == 0


def ax_set_attribute(element: AXUIElementRef, attribute_name: str, value: Any) -> bool:
    """Set an attribute value on an accessibility element.

    Common settable attributes:
    - AXFocused: Set keyboard focus (bool)
    - AXValue: Set element value (str for text fields, bool for checkboxes)
    - AXSelected: Set selection state (bool)
    - AXSelectedTextRange: Set text selection (CFRange)

    Args:
        element: The accessibility element to modify
        attribute_name: Name of the attribute to set
        value: The value to set

    Returns:
        True if successful, False otherwise
    """
    error_code: int = AXUIElementSetAttributeValue(element, attribute_name, value)
    if error_code != 0:
        error_name: str = AX_ERROR_NAMES.get(error_code, f"Unknown error {error_code}")
        logger.debug(f"ax_set_attribute({attribute_name}) failed: {error_name}")
    return error_code == 0
