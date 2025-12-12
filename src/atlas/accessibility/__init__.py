"""macOS Accessibility Hierarchy Inspector

A functional programming library for traversing, searching, and analyzing
macOS application accessibility hierarchies.

Architecture:
    - types: Type definitions (TypedDicts, dataclasses)
    - constants: Immutable configuration values and attribute profiles
    - pure: Pure utility functions (no side effects)
    - predicates: Predicate factory functions for element matching
    - api: macOS Accessibility API wrappers (ax_* functions)
    - search: Hierarchy traversal and search functions
    - conversion: Converting live elements to dictionaries
    - effects: Side-effectful functions (effect_* prefix)

Example usage:
    from atlas.accessibility import (
        ax_get_running_applications,
        find_application_by_name,
        convert_application,
        find_web_areas,
        effect_export_hierarchy,
        ConversionConfig,
        AttributeProfile,
    )

    # Find and convert an application
    apps = ax_get_running_applications()
    app = find_application_by_name("Safari")

    if app:
        config = ConversionConfig(
            maximum_depth=15,
            attributes_to_capture=AttributeProfile.WEB_FOCUSED,
        )
        hierarchy = convert_application(app["process_id"], config)

        # Search the hierarchy
        web_areas = find_web_areas(hierarchy)

        # Export to file
        effect_export_hierarchy(app["process_id"], Path("hierarchy.json"), config)
"""

from atlas.accessibility._types import AXUIElementRef  # Type aliases; TypedDicts; Dataclasses
from atlas.accessibility._types import AccessibilityElementDict
from atlas.accessibility._types import ApplicationInfo
from atlas.accessibility._types import BoundsDict
from atlas.accessibility._types import ConversionConfig
from atlas.accessibility._types import PointDict
from atlas.accessibility._types import RangeDict
from atlas.accessibility._types import SearchResult
from atlas.accessibility._types import SizeDict
from atlas.accessibility.api import ax_create_application_element  # Core attribute access; Element creation; Value extraction; Parameter creation; Text helpers; Application management; UI interaction
from atlas.accessibility.api import ax_create_cfrange
from atlas.accessibility.api import ax_create_cgpoint
from atlas.accessibility.api import ax_create_system_wide_element
from atlas.accessibility.api import ax_extract_point
from atlas.accessibility.api import ax_extract_range
from atlas.accessibility.api import ax_extract_size
from atlas.accessibility.api import ax_get_action_names
from atlas.accessibility.api import ax_get_attribute
from atlas.accessibility.api import ax_get_attribute_names
from atlas.accessibility.api import ax_get_bounds_for_range
from atlas.accessibility.api import ax_get_cell_at_position
from atlas.accessibility.api import ax_get_element_at_position
from atlas.accessibility.api import ax_get_focused_element
from atlas.accessibility.api import ax_get_line_for_index
from atlas.accessibility.api import ax_get_parameterized_attribute
from atlas.accessibility.api import ax_get_parameterized_attribute_names
from atlas.accessibility.api import ax_get_range_for_line
from atlas.accessibility.api import ax_get_range_for_position
from atlas.accessibility.api import ax_get_running_applications
from atlas.accessibility.api import ax_get_string_for_range
from atlas.accessibility.api import ax_get_valid_windows
from atlas.accessibility.api import ax_perform_action
from atlas.accessibility.api import ax_set_attribute
from atlas.accessibility.constants import ALL_STANDARD_ATTRIBUTES  # Attribute groups; Special sets; Role constants; Profiles
from atlas.accessibility.constants import AXROLE_APPLICATION
from atlas.accessibility.constants import AXROLE_BUTTON
from atlas.accessibility.constants import AXROLE_GROUP
from atlas.accessibility.constants import AXROLE_LINK
from atlas.accessibility.constants import AXROLE_LIST
from atlas.accessibility.constants import AXROLE_SCROLL_AREA
from atlas.accessibility.constants import AXROLE_STATIC_TEXT
from atlas.accessibility.constants import AXROLE_TEXT_AREA
from atlas.accessibility.constants import AXROLE_TEXT_FIELD
from atlas.accessibility.constants import AXROLE_WEB_AREA
from atlas.accessibility.constants import AXROLE_WINDOW
from atlas.accessibility.constants import AttributeProfile
from atlas.accessibility.constants import CIRCULAR_REFERENCE_ATTRIBUTES
from atlas.accessibility.constants import CORE_ATTRIBUTES
from atlas.accessibility.constants import DEFAULT_ATTRIBUTES
from atlas.accessibility.constants import EXTENDED_TEXT_ATTRIBUTES
from atlas.accessibility.constants import INTERACTIVE_ROLES
from atlas.accessibility.constants import LINK_ATTRIBUTES
from atlas.accessibility.constants import STATE_ATTRIBUTES
from atlas.accessibility.constants import WEB_ATTRIBUTES
from atlas.accessibility.conversion import convert_application
from atlas.accessibility.conversion import convert_element
from atlas.accessibility.conversion import convert_element_at_position
from atlas.accessibility.conversion import convert_focused_element
from atlas.accessibility.effects import effect_export_hierarchy  # File I/O; Logging
from atlas.accessibility.effects import effect_load_hierarchy
from atlas.accessibility.effects import effect_log_applications
from atlas.accessibility.effects import effect_log_debug
from atlas.accessibility.effects import effect_log_error
from atlas.accessibility.effects import effect_log_export_success
from atlas.accessibility.effects import effect_log_hierarchy_stats
from atlas.accessibility.effects import effect_log_info
from atlas.accessibility.effects import effect_log_search_summary
from atlas.accessibility.effects import effect_log_success
from atlas.accessibility.effects import effect_log_warning
from atlas.accessibility.effects import effect_read_from_file
from atlas.accessibility.effects import effect_read_json_from_file
from atlas.accessibility.effects import effect_write_json_to_file
from atlas.accessibility.effects import effect_write_to_file
from atlas.accessibility.predicates import combine_predicates_and  # Dict predicate factories; Built-in predicates; Live predicate factories; Combinators
from atlas.accessibility.predicates import combine_predicates_or
from atlas.accessibility.predicates import create_attribute_predicate
from atlas.accessibility.predicates import create_identifier_predicate
from atlas.accessibility.predicates import create_live_identifier_predicate
from atlas.accessibility.predicates import create_live_role_predicate
from atlas.accessibility.predicates import create_live_title_predicate
from atlas.accessibility.predicates import create_live_value_predicate
from atlas.accessibility.predicates import create_role_and_title_predicate
from atlas.accessibility.predicates import create_role_predicate
from atlas.accessibility.predicates import create_subrole_predicate
from atlas.accessibility.predicates import create_title_predicate
from atlas.accessibility.predicates import create_value_predicate
from atlas.accessibility.predicates import has_children
from atlas.accessibility.predicates import has_title
from atlas.accessibility.predicates import has_url
from atlas.accessibility.predicates import has_value
from atlas.accessibility.predicates import is_enabled
from atlas.accessibility.predicates import is_focused
from atlas.accessibility.predicates import is_interactive
from atlas.accessibility.predicates import is_web_area
from atlas.accessibility.predicates import negate_predicate
from atlas.accessibility.pure import coerce_to_string
from atlas.accessibility.pure import collect_unique_roles
from atlas.accessibility.pure import count_elements_in_hierarchy
from atlas.accessibility.pure import deserialize_from_json
from atlas.accessibility.pure import element_hash
from atlas.accessibility.pure import get_hierarchy_depth
from atlas.accessibility.pure import normalize_for_comparison
from atlas.accessibility.pure import serialize_to_json
from atlas.accessibility.search import extract_elements  # Core traversal; By attribute; Web content; Interactive elements; Live search; Backward compatibility alias
from atlas.accessibility.search import find_buttons
from atlas.accessibility.search import find_by_attribute
from atlas.accessibility.search import find_by_identifier
from atlas.accessibility.search import find_by_predicate
from atlas.accessibility.search import find_by_role
from atlas.accessibility.search import find_by_subrole
from atlas.accessibility.search import find_by_title
from atlas.accessibility.search import find_by_value
from atlas.accessibility.search import find_elements_with_url
from atlas.accessibility.search import find_first_by_predicate
from atlas.accessibility.search import find_innermost_web_area_with_title
from atlas.accessibility.search import find_interactive_elements
from atlas.accessibility.search import find_links
from atlas.accessibility.search import find_live
from atlas.accessibility.search import find_live_by_identifier
from atlas.accessibility.search import find_live_by_predicate
from atlas.accessibility.search import find_live_by_role
from atlas.accessibility.search import find_live_by_subrole
from atlas.accessibility.search import find_live_by_title
from atlas.accessibility.search import find_live_first
from atlas.accessibility.search import find_live_innermost_web_area_with_title
from atlas.accessibility.search import find_live_web_area
from atlas.accessibility.search import find_static_text
from atlas.accessibility.search import find_text_areas
from atlas.accessibility.search import find_text_fields
from atlas.accessibility.search import find_web_areas
from atlas.accessibility.search import navigate_to_path
from atlas.accessibility.search import traverse_with_predicate


# Convenience aliases
find_application_by_name = None  # Defined below to avoid circular import


def find_application_by_name(
    name_substring: str,
    case_sensitive: bool = False,
) -> ApplicationInfo | None:
    """Find a running application by name substring.

    Args:
        name_substring: Substring to search for in application names
        case_sensitive: Whether to perform case-sensitive matching

    Returns:
        ApplicationInfo for the first matching application, or None
    """
    from atlas.accessibility.pure import normalize_for_comparison

    apps: list[ApplicationInfo] = ax_get_running_applications()
    normalized_search: str = normalize_for_comparison(name_substring, case_sensitive)

    for app in apps:
        normalized_name: str = normalize_for_comparison(app["name"], case_sensitive)
        if normalized_search in normalized_name:
            return app

    return None


def analyze_hierarchy(hierarchy: AccessibilityElementDict) -> dict:
    """Analyze a hierarchy and return statistics and findings.

    Args:
        hierarchy: The hierarchy to analyze

    Returns:
        Dictionary containing analysis results
    """
    web_areas: list[AccessibilityElementDict] = find_web_areas(hierarchy)
    interactive: list[AccessibilityElementDict] = find_interactive_elements(hierarchy)
    urls: list[AccessibilityElementDict] = find_elements_with_url(hierarchy)
    innermost: AccessibilityElementDict | None = find_innermost_web_area_with_title(hierarchy)

    return {
        "element_count": count_elements_in_hierarchy(hierarchy),
        "max_depth": get_hierarchy_depth(hierarchy),
        "unique_roles": collect_unique_roles(hierarchy),
        "web_areas_count": len(web_areas),
        "interactive_count": len(interactive),
        "urls_count": len(urls),
        "innermost_web_area_title": innermost.get("AXTitle") if innermost else None,
        "web_areas": web_areas,
        "interactive_elements": interactive,
        "elements_with_urls": urls,
    }


__all__ = [
    # Types
    "AXUIElementRef",
    "PointDict",
    "SizeDict",
    "RangeDict",
    "BoundsDict",
    "ApplicationInfo",
    "AccessibilityElementDict",
    "SearchResult",
    "ConversionConfig",
    # Constants
    "CORE_ATTRIBUTES",
    "STATE_ATTRIBUTES",
    "EXTENDED_TEXT_ATTRIBUTES",
    "WEB_ATTRIBUTES",
    "LINK_ATTRIBUTES",
    "ALL_STANDARD_ATTRIBUTES",
    "DEFAULT_ATTRIBUTES",
    "CIRCULAR_REFERENCE_ATTRIBUTES",
    "INTERACTIVE_ROLES",
    "AXROLE_WEB_AREA",
    "AXROLE_APPLICATION",
    "AXROLE_WINDOW",
    "AXROLE_BUTTON",
    "AXROLE_TEXT_FIELD",
    "AXROLE_TEXT_AREA",
    "AXROLE_STATIC_TEXT",
    "AXROLE_LINK",
    "AXROLE_GROUP",
    "AXROLE_LIST",
    "AXROLE_SCROLL_AREA",
    "AttributeProfile",
    # Pure functions
    "coerce_to_string",
    "normalize_for_comparison",
    "element_hash",
    "serialize_to_json",
    "deserialize_from_json",
    "count_elements_in_hierarchy",
    "get_hierarchy_depth",
    "collect_unique_roles",
    # Predicates
    "create_attribute_predicate",
    "create_role_predicate",
    "create_subrole_predicate",
    "create_title_predicate",
    "create_identifier_predicate",
    "create_value_predicate",
    "create_role_and_title_predicate",
    "has_url",
    "is_interactive",
    "is_web_area",
    "is_enabled",
    "is_focused",
    "has_children",
    "has_title",
    "has_value",
    "create_live_role_predicate",
    "create_live_title_predicate",
    "create_live_identifier_predicate",
    "create_live_value_predicate",
    "combine_predicates_and",
    "combine_predicates_or",
    "negate_predicate",
    # API functions
    "ax_get_attribute",
    "ax_get_attribute_names",
    "ax_get_parameterized_attribute_names",
    "ax_get_parameterized_attribute",
    "ax_create_application_element",
    "ax_create_system_wide_element",
    "ax_extract_point",
    "ax_extract_size",
    "ax_extract_range",
    "ax_create_cfrange",
    "ax_create_cgpoint",
    "ax_get_string_for_range",
    "ax_get_line_for_index",
    "ax_get_range_for_line",
    "ax_get_bounds_for_range",
    "ax_get_range_for_position",
    "ax_get_cell_at_position",
    "ax_get_element_at_position",
    "ax_get_running_applications",
    "ax_get_valid_windows",
    "ax_get_focused_element",
    "ax_get_action_names",
    "ax_perform_action",
    "ax_set_attribute",
    # Search functions
    "traverse_with_predicate",
    "find_by_predicate",
    "find_first_by_predicate",
    "extract_elements",
    "navigate_to_path",
    "find_by_role",
    "find_by_subrole",
    "find_by_title",
    "find_by_identifier",
    "find_by_value",
    "find_by_attribute",
    "find_web_areas",
    "find_innermost_web_area_with_title",
    "find_elements_with_url",
    "find_interactive_elements",
    "find_buttons",
    "find_links",
    "find_text_fields",
    "find_text_areas",
    "find_static_text",
    "find_live",
    "find_live_first",
    "find_live_by_predicate",
    "find_live_by_role",
    "find_live_by_subrole",
    "find_live_by_title",
    "find_live_by_identifier",
    "find_live_web_area",
    "find_live_innermost_web_area_with_title",
    "find_articles",
    # Conversion functions
    "convert_element",
    "convert_application",
    "convert_focused_element",
    "convert_element_at_position",
    # Effect functions
    "effect_write_to_file",
    "effect_read_from_file",
    "effect_write_json_to_file",
    "effect_read_json_from_file",
    "effect_export_hierarchy",
    "effect_load_hierarchy",
    "effect_log_debug",
    "effect_log_info",
    "effect_log_warning",
    "effect_log_error",
    "effect_log_success",
    "effect_log_applications",
    "effect_log_search_summary",
    "effect_log_export_success",
    "effect_log_hierarchy_stats",
    # Convenience functions
    "find_application_by_name",
    "analyze_hierarchy",
]
