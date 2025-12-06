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


# Type alias for the opaque AXUIElement reference
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
    AXRole: str
    AXRoleDescription: str
    AXTitle: str
    AXDescription: str
    AXValue: str
    AXIdentifier: str
    AXLabel: str
    position: PointDictionary
    size: SizeDictionary
    children: list[AccessibilityElementDictionary]
    truncated: bool


DEFAULT_ACCESSIBILITY_ATTRIBUTES: tuple[str, ...] = (
    "AXRole",
    "AXRoleDescription",
    "AXTitle",
    "AXDescription",
    "AXValue",
    "AXIdentifier",
    "AXLabel",
)

DEFAULT_MAXIMUM_HIERARCHY_DEPTH: int = 10


def get_accessibility_element_attribute_value(element: AXUIElementRef, attribute_name: str) -> Any | None:
    """Retrieve a single attribute value from an accessibility element."""
    error_code: int
    attribute_value: Any
    error_code, attribute_value = AXUIElementCopyAttributeValue(
        element, attribute_name, None
    )

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


def convert_accessibility_element_to_dictionary(
    element: AXUIElementRef,
    maximum_depth: int = DEFAULT_MAXIMUM_HIERARCHY_DEPTH,
    current_depth: int = 0,
) -> AccessibilityElementDictionary:
    """Recursively convert an accessibility element and its children to a dictionary."""
    if current_depth >= maximum_depth:
        return {"truncated": True}

    element_dictionary: AccessibilityElementDictionary = {}

    for attribute_name in DEFAULT_ACCESSIBILITY_ATTRIBUTES:
        attribute_value: Any | None = get_accessibility_element_attribute_value(element, attribute_name)
        if attribute_value is not None:
            element_dictionary[attribute_name] = str(attribute_value)

    position_value_reference: Any | None = get_accessibility_element_attribute_value(
        element, "AXPosition"
    )
    if position_value_reference is not None:
        position_dictionary: PointDictionary | None = (
            extract_point_from_accessibility_value_reference(position_value_reference)
        )
        if position_dictionary is not None:
            element_dictionary["position"] = position_dictionary

    size_value_reference: Any | None = get_accessibility_element_attribute_value(
        element, "AXSize"
    )
    if size_value_reference is not None:
        size_dictionary: SizeDictionary | None = (
            extract_size_from_accessibility_value_reference(size_value_reference)
        )
        if size_dictionary is not None:
            element_dictionary["size"] = size_dictionary

    child_elements: Any | None = get_accessibility_element_attribute_value(
        element, "AXChildren"
    )
    if child_elements and len(child_elements) > 0:
        children_dictionaries: list[AccessibilityElementDictionary] = []
        for child_index in range(len(child_elements)):
            child_element: AXUIElementRef = child_elements[child_index]
            child_dictionary: AccessibilityElementDictionary = (
                convert_accessibility_element_to_dictionary(
                    child_element, maximum_depth, current_depth + 1
                )
            )
            children_dictionaries.append(child_dictionary)
        element_dictionary["children"] = children_dictionaries

    return element_dictionary


def get_running_applications_with_regular_activation_policy() -> list[ApplicationInfo]:
    """Retrieve all running applications that have a regular activation policy.

    Regular activation policy indicates standard GUI applications that appear
    in the Dock and can be activated by the user.
    """
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
) -> AccessibilityElementDictionary:
    """Retrieve the full accessibility hierarchy for an application by its process ID."""
    application_element: AXUIElementRef = create_accessibility_element_for_application(
        process_id
    )
    return convert_accessibility_element_to_dictionary(
        application_element, maximum_depth
    )


def get_system_wide_focused_element_hierarchy(maximum_depth: int = 3) -> AccessibilityElementDictionary | None:
    """Retrieve the currently focused accessibility element system-wide."""
    system_wide_element: AXUIElementRef = create_system_wide_accessibility_element()
    focused_element: Any | None = get_accessibility_element_attribute_value(
        system_wide_element, "AXFocusedUIElement"
    )

    if focused_element is not None:
        return convert_accessibility_element_to_dictionary(
            focused_element, maximum_depth
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
) -> AccessibilityElementDictionary:
    """Export an application's accessibility hierarchy to a JSON file.

    This is a convenience function that combines hierarchy retrieval,
    serialization, and file writing.
    """
    hierarchy_dictionary: AccessibilityElementDictionary = get_application_accessibility_hierarchy(
        process_id=process_id, maximum_depth=maximum_depth
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


def main() -> None:
    """Main entry point for the accessibility hierarchy inspector.

    Lists running applications and exports the hierarchy of a target application.
    """
    target_application_name_substring: str = "atlas"
    output_file_path: Path = Path("hierarchy.json")
    hierarchy_maximum_depth: int = 5

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

    hierarchy_dictionary: AccessibilityElementDictionary = (
        export_application_hierarchy_to_json_file(
            matching_application["process_id"],
            output_file_path,
            hierarchy_maximum_depth,
        )
    )

    logger.debug(f"Hierarchy preview:\n{serialize_hierarchy_to_json_string(hierarchy_dictionary)}")

    logger.success(
        f"Successfully exported hierarchy for '{matching_application['name']}' "
        f"to {output_file_path.resolve()}"
    )


if __name__ == "__main__":
    main()
