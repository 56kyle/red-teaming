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

from atlas.accessibility._types import (
    # Type aliases
    AXUIElementRef,
    # TypedDicts
    PointDict,
    SizeDict,
    RangeDict,
    BoundsDict,
    ApplicationInfo,
    AccessibilityElementDict,
    SearchResult,
    # Dataclasses
    ConversionConfig,
)

from atlas.accessibility.constants import (
    # Attribute groups
    CORE_ATTRIBUTES,
    STATE_ATTRIBUTES,
    EXTENDED_TEXT_ATTRIBUTES,
    WEB_ATTRIBUTES,
    LINK_ATTRIBUTES,
    ALL_STANDARD_ATTRIBUTES,
    DEFAULT_ATTRIBUTES,
    # Special sets
    CIRCULAR_REFERENCE_ATTRIBUTES,
    INTERACTIVE_ROLES,
    # Role constants
    AXROLE_WEB_AREA,
    AXROLE_APPLICATION,
    AXROLE_WINDOW,
    AXROLE_BUTTON,
    AXROLE_TEXT_FIELD,
    AXROLE_TEXT_AREA,
    AXROLE_STATIC_TEXT,
    AXROLE_LINK,
    AXROLE_GROUP,
    AXROLE_LIST,
    AXROLE_SCROLL_AREA,
    # Profiles
    AttributeProfile,
)

from atlas.accessibility.pure import (
    coerce_to_string,
    normalize_for_comparison,
    element_hash,
    serialize_to_json,
    deserialize_from_json,
    count_elements_in_hierarchy,
    get_hierarchy_depth,
    collect_unique_roles,
)

from atlas.accessibility.predicates import (
    # Dict predicate factories
    create_attribute_predicate,
    create_role_predicate,
    create_subrole_predicate,
    create_title_predicate,
    create_identifier_predicate,
    create_value_predicate,
    create_role_and_title_predicate,
    # Built-in predicates
    has_url,
    is_interactive,
    is_web_area,
    is_enabled,
    is_focused,
    has_children,
    has_title,
    has_value,
    # Live predicate factories
    create_live_role_predicate,
    create_live_title_predicate,
    create_live_identifier_predicate,
    create_live_value_predicate,
    # Combinators
    combine_predicates_and,
    combine_predicates_or,
    negate_predicate,
)

from atlas.accessibility.api import (
    # Core attribute access
    ax_get_attribute,
    ax_get_attribute_names,
    ax_get_parameterized_attribute_names,
    ax_get_parameterized_attribute,
    # Element creation
    ax_create_application_element,
    ax_create_system_wide_element,
    # Value extraction
    ax_extract_point,
    ax_extract_size,
    ax_extract_range,
    # Parameter creation
    ax_create_cfrange,
    ax_create_cgpoint,
    # Text helpers
    ax_get_string_for_range,
    ax_get_line_for_index,
    ax_get_range_for_line,
    ax_get_bounds_for_range,
    ax_get_range_for_position,
    ax_get_cell_at_position,
    ax_get_element_at_position,
    # Application management
    ax_get_running_applications,
    ax_get_valid_windows,
    ax_get_focused_element,
)

from atlas.accessibility.search import (
    # Core traversal
    traverse_with_predicate,
    find_by_predicate,
    find_first_by_predicate,
    extract_elements,
    navigate_to_path,
    # By attribute
    find_by_role,
    find_by_subrole,
    find_by_title,
    find_by_identifier,
    find_by_value,
    find_by_attribute,
    # Web content
    find_web_areas,
    find_innermost_web_area_with_title,
    find_elements_with_url,
    # Interactive elements
    find_interactive_elements,
    find_buttons,
    find_links,
    find_text_fields,
    find_text_areas,
    find_static_text,
    # Live search
    find_live_by_predicate,
    find_live_by_role,
    find_live_by_title,
    find_live_by_identifier,
    find_live_web_area,
)

from atlas.accessibility.conversion import (
    convert_element,
    convert_application,
    convert_focused_element,
    convert_element_at_position,
)

from atlas.accessibility.effects import (
    # File I/O
    effect_write_to_file,
    effect_read_from_file,
    effect_write_json_to_file,
    effect_read_json_from_file,
    effect_export_hierarchy,
    effect_load_hierarchy,
    # Logging
    effect_log_debug,
    effect_log_info,
    effect_log_warning,
    effect_log_error,
    effect_log_success,
    effect_log_applications,
    effect_log_search_summary,
    effect_log_export_success,
    effect_log_hierarchy_stats,
)


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
    "find_live_by_predicate",
    "find_live_by_role",
    "find_live_by_title",
    "find_live_by_identifier",
    "find_live_web_area",
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
