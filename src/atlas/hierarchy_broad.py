"""Module for traversing and exporting the accessibility UI element hierarchy of running macOS applications."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict

from loguru import logger


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


class ApplicationInfo(TypedDict):
    name: str
    process_id: int
    bundle_identifier: str | None


class AccessibilityElementDictionary(TypedDict, total=False):
    # Identity & Role
    AXRole: str
    AXSubrole: str
    AXRoleDescription: str
    AXIdentifier: str

    # Labels & Text
    AXTitle: str
    AXDescription: str
    AXLabel: str
    AXValue: str
    AXValueDescription: str
    AXHelp: str
    AXPlaceholderValue: str

    # State
    AXEnabled: str
    AXFocused: str
    AXSelected: str
    AXExpanded: str
    AXRequired: str
    AXElementBusy: str
    AXVisited: str

    # Web-specific
    AXURL: str
    AXDOMIdentifier: str
    AXDOMClassList: str

    # Geometry
    position: PointDictionary
    size: SizeDictionary

    # Hierarchy
    children: list[AccessibilityElementDictionary]
    windows: list[AccessibilityElementDictionary]

    # Meta
    truncated: bool
    cycle_detected: bool
    available_attributes: list[str]


# Core attributes - always captured (identity, labels, basic info)
CORE_ATTRIBUTES: tuple[str, ...] = (
    "AXRole",
    "AXSubrole",
    "AXRoleDescription",
    "AXIdentifier",
    "AXTitle",
    "AXDescription",
    "AXLabel",
    "AXValue",
)

# State attributes - element's current state
STATE_ATTRIBUTES: tuple[str, ...] = (
    "AXEnabled",
    "AXFocused",
    "AXSelected",
    "AXExpanded",
    "AXRequired",
    "AXElementBusy",
)

# Extended text attributes - additional text content
EXTENDED_TEXT_ATTRIBUTES: tuple[str, ...] = (
    "AXValueDescription",
    "AXHelp",
    "AXPlaceholderValue",
)

# Web-specific attributes - useful for Chromium/web content
WEB_ATTRIBUTES: tuple[str, ...] = (
    "AXURL",
    "AXDOMIdentifier",
    "AXDOMClassList",
    "AXVisited",
)

# Link-related attributes
LINK_ATTRIBUTES: tuple[str, ...] = (
    "AXURL",
    "AXVisited",
)

# All standard attributes combined
ALL_STANDARD_ATTRIBUTES: tuple[str, ...] = (
    CORE_ATTRIBUTES
    + STATE_ATTRIBUTES
    + EXTENDED_TEXT_ATTRIBUTES
    + WEB_ATTRIBUTES
)

# Default set - core + state (good balance of info vs output size)
DEFAULT_ATTRIBUTES: tuple[str, ...] = CORE_ATTRIBUTES + STATE_ATTRIBUTES

CIRCULAR_REFERENCE_ATTRIBUTES: frozenset[str] = frozenset(
    {
        "AXParent",
        "AXTopLevelUIElement",
        "AXWindow",
        "AXMainWindow",
        "AXFocusedWindow",
        "AXWindows",
        "AXFocusedUIElement",
        "AXSharedFocusElements",
    }
)

WINDOW_RETRIEVAL_ATTRIBUTES: tuple[str, ...] = (
    "AXFocusedWindow",
    "AXMainWindow",
    "AXWindows",
)

AXROLE_WEB_AREA: str = "AXWebArea"

DEFAULT_MAXIMUM_HIERARCHY_DEPTH: int = 10


class AttributeProfile:
    """Predefined attribute collection profiles for different use cases."""

    MINIMAL: tuple[str, ...] = (
        "AXRole",
        "AXSubrole",
        "AXTitle",
        "AXIdentifier",
    )

    DEFAULT: tuple[str, ...] = DEFAULT_ATTRIBUTES

    WEB_FOCUSED: tuple[str, ...] = CORE_ATTRIBUTES + STATE_ATTRIBUTES + WEB_ATTRIBUTES

    FULL: tuple[str, ...] = ALL_STANDARD_ATTRIBUTES


def get_accessibility_element_attribute_value(element: AXUIElementRef, attribute_name: str) -> Any | None:
    """Retrieve a single attribute value from an accessibility element."""
    error_code: int
    attribute_value: Any
    error_code, attribute_value = AXUIElementCopyAttributeValue(element, attribute_name, None)

    if error_code == 0:
        return attribute_value
    return None


def get_accessibility_element_attribute_names(element: AXUIElementRef) -> list[str]:
    """Retrieve all available attribute names for an accessibility element."""
    error_code: int
    attribute_names: Any
    error_code, attribute_names = AXUIElementCopyAttributeNames(element, None)

    if error_code == 0:
        return list(attribute_names)
    return []


def get_accessibility_element_hash(element: AXUIElementRef) -> int:
    """Generate a hash for an accessibility element for cycle detection."""
    return hash(element)


def extract_point_from_accessibility_value_reference(value_reference: Any) -> PointDictionary | None:
    """Extract a CGPoint from an AXValueRef containing position data."""
    extraction_succeeded: bool
    point: Any
    extraction_succeeded, point = AXValueGetValue(value_reference, kAXValueTypeCGPoint, None)

    if extraction_succeeded:
        return PointDictionary(x=point.x, y=point.y)
    return None


def extract_size_from_accessibility_value_reference(value_reference: Any) -> SizeDictionary | None:
    """Extract a CGSize from an AXValueRef containing size data."""
    extraction_succeeded: bool
    size: Any
    extraction_succeeded, size = AXValueGetValue(value_reference, kAXValueTypeCGSize, None)

    if extraction_succeeded:
        return SizeDictionary(width=size.width, height=size.height)
    return None


def coerce_attribute_value_to_string(value: Any) -> str:
    """Convert an attribute value to a string representation."""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    return str(value)


def get_windows_from_application_element(application_element: AXUIElementRef) -> list[AXUIElementRef]:
    """Retrieve window elements from an application, with fallbacks for Chromium-based apps."""
    # Try focused/main window first (more reliable for Chromium-based apps)
    for window_attribute in ("AXFocusedWindow", "AXMainWindow"):
        window_value: Any | None = get_accessibility_element_attribute_value(application_element, window_attribute)

        if window_value is not None:
            attribute_names: list[str] = get_accessibility_element_attribute_names(window_value)
            if len(attribute_names) > 0:
                logger.debug(
                    f"Window attribute {window_attribute} returned valid element with {len(attribute_names)} attributes"
                )
                return [window_value]
            else:
                logger.debug(f"Window attribute {window_attribute} returned element with no attributes, skipping")

    # Fall back to AXWindows
    windows_value: Any | None = get_accessibility_element_attribute_value(application_element, "AXWindows")

    if windows_value is not None:
        try:
            window_count: int = len(windows_value)
            logger.debug(f"AXWindows returned collection with {window_count} elements")

            if window_count > 0:
                valid_windows: list[AXUIElementRef] = []
                for i in range(window_count):
                    window_element: AXUIElementRef = windows_value[i]
                    attribute_names: list[str] = get_accessibility_element_attribute_names(window_element)
                    if len(attribute_names) > 0:
                        valid_windows.append(window_element)
                        logger.debug(f"AXWindows[{i}] is valid with {len(attribute_names)} attributes")
                    else:
                        logger.debug(f"AXWindows[{i}] has no attributes, skipping")

                if valid_windows:
                    return valid_windows
        except TypeError:
            logger.debug("AXWindows value is not iterable")

    logger.warning("No valid windows found via any retrieval method")
    return []


def convert_accessibility_element_to_dictionary(
    element: AXUIElementRef,
    maximum_depth: int = DEFAULT_MAXIMUM_HIERARCHY_DEPTH,
    current_depth: int = 0,
    visited_element_hashes: set[int] | None = None,
    include_available_attributes: bool = False,
    attributes_to_capture: tuple[str, ...] = DEFAULT_ATTRIBUTES,
) -> AccessibilityElementDictionary:
    """Recursively convert an accessibility element and its children to a dictionary."""
    if visited_element_hashes is None:
        visited_element_hashes = set()

    element_hash: int = get_accessibility_element_hash(element)

    if element_hash in visited_element_hashes:
        logger.debug(f"Cycle detected at depth {current_depth}, element hash: {element_hash}")
        return {"cycle_detected": True}

    visited_element_hashes.add(element_hash)

    if current_depth >= maximum_depth:
        return {"truncated": True}

    element_dictionary: AccessibilityElementDictionary = {}

    available_attribute_names: list[str] = get_accessibility_element_attribute_names(element)

    if include_available_attributes:
        element_dictionary["available_attributes"] = available_attribute_names

    if current_depth <= 2:
        logger.debug(
            f"Depth {current_depth}: Element has {len(available_attribute_names)} attributes: {available_attribute_names[:10]}..."
        )

    # Capture requested attributes
    for attribute_name in attributes_to_capture:
        attribute_value: Any | None = get_accessibility_element_attribute_value(element, attribute_name)
        if attribute_value is not None:
            element_dictionary[attribute_name] = coerce_attribute_value_to_string(attribute_value)

    # Position and size (special handling for AXValueRef)
    position_value_reference: Any | None = get_accessibility_element_attribute_value(element, "AXPosition")
    if position_value_reference is not None:
        position_dictionary: PointDictionary | None = extract_point_from_accessibility_value_reference(
            position_value_reference
        )
        if position_dictionary is not None:
            element_dictionary["position"] = position_dictionary

    size_value_reference: Any | None = get_accessibility_element_attribute_value(element, "AXSize")
    if size_value_reference is not None:
        size_dictionary: SizeDictionary | None = extract_size_from_accessibility_value_reference(size_value_reference)
        if size_dictionary is not None:
            element_dictionary["size"] = size_dictionary

    # Recursively process children
    child_elements: Any | None = get_accessibility_element_attribute_value(element, "AXChildren")
    if child_elements and len(child_elements) > 0:
        children_dictionaries: list[AccessibilityElementDictionary] = []
        for child_element in child_elements:
            child_dictionary: AccessibilityElementDictionary = convert_accessibility_element_to_dictionary(
                child_element,
                maximum_depth,
                current_depth + 1,
                visited_element_hashes,
                include_available_attributes,
                attributes_to_capture,
            )
            children_dictionaries.append(child_dictionary)
        element_dictionary["children"] = children_dictionaries

    return element_dictionary


def convert_application_element_to_dictionary(
    application_element: AXUIElementRef,
    maximum_depth: int = DEFAULT_MAXIMUM_HIERARCHY_DEPTH,
    include_windows_as_children: bool = True,
    include_available_attributes: bool = False,
    attributes_to_capture: tuple[str, ...] = DEFAULT_ATTRIBUTES,
) -> AccessibilityElementDictionary:
    """Convert an application accessibility element to a dictionary, properly handling windows."""
    children_visited_hashes: set[int] = set()

    element_dictionary: AccessibilityElementDictionary = convert_accessibility_element_to_dictionary(
        application_element,
        maximum_depth,
        0,
        children_visited_hashes,
        include_available_attributes,
        attributes_to_capture,
    )

    window_elements: list[AXUIElementRef] = get_windows_from_application_element(application_element)
    logger.info(f"Retrieved {len(window_elements)} window element(s)")

    if window_elements:
        window_dictionaries: list[AccessibilityElementDictionary] = []

        for window_index, window_element in enumerate(window_elements):
            window_visited_hashes: set[int] = set()

            window_hash: int = get_accessibility_element_hash(window_element)
            logger.debug(f"Window {window_index} hash: {window_hash}")

            window_attributes: list[str] = get_accessibility_element_attribute_names(window_element)
            logger.info(f"Window {window_index} has {len(window_attributes)} attributes: {window_attributes}")

            window_dictionary: AccessibilityElementDictionary = convert_accessibility_element_to_dictionary(
                window_element,
                maximum_depth,
                1,
                window_visited_hashes,
                include_available_attributes,
                attributes_to_capture,
            )

            logger.debug(f"Window {window_index} converted to dict with keys: {list(window_dictionary.keys())}")
            window_dictionaries.append(window_dictionary)

        if include_windows_as_children:
            existing_children: list[AccessibilityElementDictionary] = element_dictionary.get("children", [])
            element_dictionary["children"] = existing_children + window_dictionaries
        else:
            element_dictionary["windows"] = window_dictionaries

    return element_dictionary


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


def create_system_wide_accessibility_element() -> AXUIElementRef:
    """Create a system-wide accessibility element reference."""
    return AXUIElementCreateSystemWide()


def get_application_accessibility_hierarchy(
    process_id: int,
    maximum_depth: int = DEFAULT_MAXIMUM_HIERARCHY_DEPTH,
    include_windows_as_children: bool = True,
    include_available_attributes: bool = False,
    attributes_to_capture: tuple[str, ...] = DEFAULT_ATTRIBUTES,
) -> AccessibilityElementDictionary:
    """Retrieve the full accessibility hierarchy for an application by its process ID."""
    application_element: AXUIElementRef = create_accessibility_element_for_application(process_id)
    return convert_application_element_to_dictionary(
        application_element,
        maximum_depth,
        include_windows_as_children,
        include_available_attributes,
        attributes_to_capture,
    )


def get_system_wide_focused_element_hierarchy(
    maximum_depth: int = 3,
    attributes_to_capture: tuple[str, ...] = DEFAULT_ATTRIBUTES,
) -> AccessibilityElementDictionary | None:
    """Retrieve the currently focused accessibility element system-wide."""
    system_wide_element: AXUIElementRef = create_system_wide_accessibility_element()
    focused_element: Any | None = get_accessibility_element_attribute_value(
        system_wide_element, "AXFocusedUIElement"
    )

    if focused_element is not None:
        return convert_accessibility_element_to_dictionary(
            focused_element,
            maximum_depth,
            attributes_to_capture=attributes_to_capture,
        )
    return None


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


def find_elements_by_role_in_hierarchy(
    hierarchy: AccessibilityElementDictionary,
    target_role: str,
) -> list[AccessibilityElementDictionary]:
    """Recursively find all elements with a specific AXRole in a hierarchy."""
    matching_elements: list[AccessibilityElementDictionary] = []

    if hierarchy.get("AXRole") == target_role:
        matching_elements.append(hierarchy)

    for child in hierarchy.get("children", []):
        matching_elements.extend(find_elements_by_role_in_hierarchy(child, target_role))

    for window in hierarchy.get("windows", []):
        matching_elements.extend(find_elements_by_role_in_hierarchy(window, target_role))

    return matching_elements


def find_elements_by_subrole_in_hierarchy(
    hierarchy: AccessibilityElementDictionary,
    target_subrole: str,
) -> list[AccessibilityElementDictionary]:
    """Recursively find all elements with a specific AXSubrole in a hierarchy."""
    matching_elements: list[AccessibilityElementDictionary] = []

    if hierarchy.get("AXSubrole") == target_subrole:
        matching_elements.append(hierarchy)

    for child in hierarchy.get("children", []):
        matching_elements.extend(find_elements_by_subrole_in_hierarchy(child, target_subrole))

    for window in hierarchy.get("windows", []):
        matching_elements.extend(find_elements_by_subrole_in_hierarchy(window, target_subrole))

    return matching_elements


def find_web_area_elements_in_hierarchy(
    hierarchy: AccessibilityElementDictionary,
) -> list[AccessibilityElementDictionary]:
    """Recursively find all AXWebArea elements in a hierarchy."""
    return find_elements_by_role_in_hierarchy(hierarchy, AXROLE_WEB_AREA)


def find_innermost_web_area_with_title(
    hierarchy: AccessibilityElementDictionary,
) -> AccessibilityElementDictionary | None:
    """Find the innermost AXWebArea that has a title (typically the actual page content)."""
    web_areas: list[AccessibilityElementDictionary] = find_web_area_elements_in_hierarchy(hierarchy)

    for web_area in reversed(web_areas):
        if web_area.get("AXTitle"):
            return web_area

    return web_areas[-1] if web_areas else None


def find_elements_with_url_in_hierarchy(
    hierarchy: AccessibilityElementDictionary,
) -> list[AccessibilityElementDictionary]:
    """Recursively find all elements that have an AXURL attribute."""
    matching_elements: list[AccessibilityElementDictionary] = []

    if hierarchy.get("AXURL"):
        matching_elements.append(hierarchy)

    for child in hierarchy.get("children", []):
        matching_elements.extend(find_elements_with_url_in_hierarchy(child))

    for window in hierarchy.get("windows", []):
        matching_elements.extend(find_elements_with_url_in_hierarchy(window))

    return matching_elements


def find_interactive_elements_in_hierarchy(
    hierarchy: AccessibilityElementDictionary,
) -> list[AccessibilityElementDictionary]:
    """Find elements that are typically interactive (buttons, links, text fields, etc.)."""
    interactive_roles: frozenset[str] = frozenset(
        {
            "AXButton",
            "AXLink",
            "AXTextField",
            "AXTextArea",
            "AXCheckBox",
            "AXRadioButton",
            "AXPopUpButton",
            "AXComboBox",
            "AXSlider",
            "AXIncrementor",
            "AXMenuButton",
            "AXDisclosureTriangle",
            "AXSwitch",
        }
    )

    matching_elements: list[AccessibilityElementDictionary] = []

    element_role: str | None = hierarchy.get("AXRole")
    if element_role in interactive_roles:
        matching_elements.append(hierarchy)

    for child in hierarchy.get("children", []):
        matching_elements.extend(find_interactive_elements_in_hierarchy(child))

    for window in hierarchy.get("windows", []):
        matching_elements.extend(find_interactive_elements_in_hierarchy(window))

    return matching_elements


def serialize_hierarchy_to_json_string(
    hierarchy_dictionary: AccessibilityElementDictionary,
    indent_spaces: int = 2,
) -> str:
    """Serialize an accessibility hierarchy dictionary to a formatted JSON string."""
    return json.dumps(hierarchy_dictionary, indent=indent_spaces, default=str)


def write_json_string_to_file(json_string: str, output_path: Path) -> None:
    """Write a JSON string to a file at the specified path."""
    output_path.write_text(json_string, encoding="utf-8")
    logger.info(f"Wrote JSON content to {output_path.resolve()}")


def export_application_hierarchy_to_json_file(
    process_id: int,
    output_path: Path,
    maximum_depth: int = DEFAULT_MAXIMUM_HIERARCHY_DEPTH,
    include_windows_as_children: bool = True,
    include_available_attributes: bool = False,
    attributes_to_capture: tuple[str, ...] = DEFAULT_ATTRIBUTES,
) -> AccessibilityElementDictionary:
    """Export an application's accessibility hierarchy to a JSON file."""
    hierarchy_dictionary: AccessibilityElementDictionary = get_application_accessibility_hierarchy(
        process_id=process_id,
        maximum_depth=maximum_depth,
        include_windows_as_children=include_windows_as_children,
        include_available_attributes=include_available_attributes,
        attributes_to_capture=attributes_to_capture,
    )
    json_string: str = serialize_hierarchy_to_json_string(hierarchy_dictionary)
    write_json_string_to_file(json_string, output_path)
    return hierarchy_dictionary


def log_running_applications_summary() -> list[ApplicationInfo]:
    """Log a summary of all running applications with regular activation policy."""
    running_applications: list[ApplicationInfo] = get_running_applications_with_regular_activation_policy()

    logger.info(f"Found {len(running_applications)} running applications:")
    for application_info in running_applications:
        logger.info(
            f"  {application_info['name']} "
            f"(PID: {application_info['process_id']}, "
            f"Bundle: {application_info['bundle_identifier']})"
        )

    return running_applications


def save_state(name: str) -> None:
    """Save the current state of the application to a json file."""
    target_application_name_substring: str = "atlas"
    output_file_path: Path = Path(name).with_suffix(".json")
    hierarchy_maximum_depth: int = 25

    log_running_applications_summary()

    matching_application: ApplicationInfo | None = find_application_info_by_name_substring(
        target_application_name_substring
    )

    if matching_application is None:
        logger.warning(f"No application found matching '{target_application_name_substring}'")
        return

    logger.info(
        f"Found matching application: {matching_application['name']} (PID: {matching_application['process_id']})"
    )

    logger.info("Extracting accessibility hierarchy...")

    # Use WEB_FOCUSED profile for Chromium-based apps
    hierarchy_dictionary: AccessibilityElementDictionary = export_application_hierarchy_to_json_file(
        matching_application["process_id"],
        output_file_path,
        hierarchy_maximum_depth,
        # include_available_attributes=True,
        attributes_to_capture=AttributeProfile.FULL,
    )

    web_areas: list[AccessibilityElementDictionary] = find_web_area_elements_in_hierarchy(hierarchy_dictionary)
    logger.info(f"Found {len(web_areas)} AXWebArea element(s)")

    innermost_web_area: AccessibilityElementDictionary | None = find_innermost_web_area_with_title(hierarchy_dictionary)
    if innermost_web_area:
        logger.info(f"Innermost web area title: {innermost_web_area.get('AXTitle', '(no title)')}")

    interactive_elements: list[AccessibilityElementDictionary] = find_interactive_elements_in_hierarchy(
        hierarchy_dictionary
    )
    logger.info(f"Found {len(interactive_elements)} interactive element(s)")

    elements_with_urls: list[AccessibilityElementDictionary] = find_elements_with_url_in_hierarchy(hierarchy_dictionary)
    logger.info(f"Found {len(elements_with_urls)} element(s) with URLs")

    logger.success(
        f"Successfully exported hierarchy for '{matching_application['name']}' to {output_file_path.resolve()}"
    )

def main() -> None:
    """Main entry point for the accessibility hierarchy inspector."""
    save_state("hierarchy_sidebar")


if __name__ == "__main__":
    main()
