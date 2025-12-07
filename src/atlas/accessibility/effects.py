"""Side-effectful functions for file I/O and logging.

All functions in this module have side effects (file operations, logging).
They are clearly named with 'effect_' prefix to distinguish them from
pure functions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger

from atlas.accessibility.conversion import convert_application
from atlas.accessibility.pure import serialize_to_json, deserialize_from_json
from atlas.accessibility._types import AccessibilityElementDict, ApplicationInfo, ConversionConfig


# =============================================================================
# FILE I/O
# =============================================================================


def effect_write_to_file(content: str, path: Path) -> None:
    """Write content to a file.

    Args:
        content: The content to write
        path: The file path
    """
    path.write_text(content, encoding="utf-8")


def effect_read_from_file(path: Path) -> str:
    """Read content from a file.

    Args:
        path: The file path

    Returns:
        The file content
    """
    return path.read_text(encoding="utf-8")


def effect_write_json_to_file(json_string: str, path: Path) -> None:
    """Write a JSON string to a file.

    Args:
        json_string: The JSON content
        path: The file path
    """
    effect_write_to_file(json_string, path)


def effect_read_json_from_file(path: Path) -> str:
    """Read a JSON string from a file.

    Args:
        path: The file path

    Returns:
        The JSON content
    """
    return effect_read_from_file(path)


def effect_export_hierarchy(
    process_id: int,
    output_path: Path,
    config: ConversionConfig = ConversionConfig(),
) -> AccessibilityElementDict:
    """Export an application's hierarchy to a JSON file.

    Args:
        process_id: The application's process ID
        output_path: Path for the output JSON file
        config: Conversion configuration

    Returns:
        The exported hierarchy dictionary
    """
    hierarchy: AccessibilityElementDict = convert_application(process_id, config)
    json_string: str = serialize_to_json(hierarchy)
    effect_write_json_to_file(json_string, output_path)
    return hierarchy


def effect_load_hierarchy(path: Path) -> AccessibilityElementDict:
    """Load a hierarchy from a JSON file.

    Args:
        path: Path to the JSON file

    Returns:
        The loaded hierarchy dictionary
    """
    json_string: str = effect_read_json_from_file(path)
    return deserialize_from_json(json_string)


# =============================================================================
# LOGGING
# =============================================================================


def effect_log_debug(message: str) -> None:
    """Log a debug message."""
    logger.debug(message)


def effect_log_info(message: str) -> None:
    """Log an info message."""
    logger.info(message)


def effect_log_warning(message: str) -> None:
    """Log a warning message."""
    logger.warning(message)


def effect_log_error(message: str) -> None:
    """Log an error message."""
    logger.error(message)


def effect_log_success(message: str) -> None:
    """Log a success message."""
    logger.success(message)


def effect_log_applications(applications: list[ApplicationInfo]) -> None:
    """Log a summary of running applications.

    Args:
        applications: List of application info dictionaries
    """
    logger.info(f"Found {len(applications)} running applications:")
    for app in applications:
        logger.info(f"  {app['name']} (PID: {app['process_id']}, Bundle: {app['bundle_identifier']})")


def effect_log_search_summary(
    web_areas_count: int,
    interactive_count: int,
    urls_count: int,
    innermost_title: str | None,
) -> None:
    """Log a summary of hierarchy search results.

    Args:
        web_areas_count: Number of web area elements found
        interactive_count: Number of interactive elements found
        urls_count: Number of elements with URLs found
        innermost_title: Title of innermost web area, if any
    """
    logger.info(f"Found {web_areas_count} AXWebArea element(s)")
    if innermost_title:
        logger.info(f"Innermost web area title: {innermost_title}")
    logger.info(f"Found {interactive_count} interactive element(s)")
    logger.info(f"Found {urls_count} element(s) with URLs")


def effect_log_export_success(app_name: str, output_path: Path) -> None:
    """Log successful hierarchy export.

    Args:
        app_name: Name of the exported application
        output_path: Path where the file was saved
    """
    logger.success(f"Successfully exported hierarchy for '{app_name}' to {output_path.resolve()}")


def effect_log_hierarchy_stats(
    element_count: int,
    max_depth: int,
    unique_roles: set[str],
) -> None:
    """Log hierarchy statistics.

    Args:
        element_count: Total number of elements
        max_depth: Maximum depth of hierarchy
        unique_roles: Set of unique roles found
    """
    logger.info(f"Hierarchy statistics:")
    logger.info(f"  Total elements: {element_count}")
    logger.info(f"  Maximum depth: {max_depth}")
    logger.info(f"  Unique roles ({len(unique_roles)}): {sorted(unique_roles)}")
