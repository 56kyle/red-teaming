"""
Example script demonstrating the accessibility package.

This script shows how to:
1. List running applications
2. Find a specific application by name
3. Export its accessibility hierarchy
4. Search for various element types
5. Analyze the hierarchy

Usage:
    python example.py [app_name]

    If no app_name is provided, defaults to "atlas"
"""

from __future__ import annotations

import sys
from pathlib import Path

from atlas.accessibility import (
    # Types
    AccessibilityElementDict,
    ApplicationInfo,
    ConversionConfig,
    SearchResult,
    # Constants
    AttributeProfile,
    # API functions
    ax_get_running_applications,
    # Search functions
    find_web_areas,
    find_innermost_web_area_with_title,
    find_interactive_elements,
    find_elements_with_url,
    find_by_attribute,
    find_by_role,
    find_by_title,
    find_buttons,
    find_text_areas,
    find_static_text,
    # Conversion
    convert_application,
    # Analysis
    analyze_hierarchy,
    # Pure functions
    count_elements_in_hierarchy,
    get_hierarchy_depth,
    collect_unique_roles,
    # Effects
    effect_export_hierarchy,
    effect_log_applications,
    effect_log_info,
    effect_log_warning,
    effect_log_success,
    effect_log_search_summary,
    effect_log_export_success,
    effect_log_hierarchy_stats,
    # Convenience
    find_application_by_name,
)


def run_example(target_app_name: str = "atlas") -> None:
    """Run the example demonstration.

    Args:
        target_app_name: Substring to search for in application names
    """
    output_file_path: Path = Path("hierarchy.json")

    # Configure hierarchy conversion
    config: ConversionConfig = ConversionConfig(
        maximum_depth=30,
        include_available_attributes=False,
        include_parameterized_attributes=False,
        attributes_to_capture=AttributeProfile.FULL,
        include_windows_as_children=True,
    )

    # ==========================================================================
    # Step 1: List running applications
    # ==========================================================================

    effect_log_info("=" * 60)
    effect_log_info("STEP 1: Listing running applications")
    effect_log_info("=" * 60)

    applications: list[ApplicationInfo] = ax_get_running_applications()
    effect_log_applications(applications)

    # ==========================================================================
    # Step 2: Find target application
    # ==========================================================================

    effect_log_info("")
    effect_log_info("=" * 60)
    effect_log_info(f"STEP 2: Finding application matching '{target_app_name}'")
    effect_log_info("=" * 60)

    matching_application: ApplicationInfo | None = find_application_by_name(target_app_name)

    if matching_application is None:
        effect_log_warning(f"No application found matching '{target_app_name}'")
        effect_log_info("Available applications:")
        for app in applications:
            effect_log_info(f"  - {app['name']}")
        return

    effect_log_success(
        f"Found: {matching_application['name']} "
        f"(PID: {matching_application['process_id']}, "
        f"Bundle: {matching_application['bundle_identifier']})"
    )

    # ==========================================================================
    # Step 3: Export hierarchy to file
    # ==========================================================================

    effect_log_info("")
    effect_log_info("=" * 60)
    effect_log_info("STEP 3: Exporting accessibility hierarchy")
    effect_log_info("=" * 60)

    effect_log_info("Extracting accessibility hierarchy...")

    hierarchy: AccessibilityElementDict = effect_export_hierarchy(
        matching_application["process_id"],
        output_file_path,
        config,
    )

    effect_log_export_success(matching_application["name"], output_file_path)

    # ==========================================================================
    # Step 4: Analyze hierarchy statistics
    # ==========================================================================

    effect_log_info("")
    effect_log_info("=" * 60)
    effect_log_info("STEP 4: Hierarchy statistics")
    effect_log_info("=" * 60)

    element_count: int = count_elements_in_hierarchy(hierarchy)
    max_depth: int = get_hierarchy_depth(hierarchy)
    unique_roles: set[str] = collect_unique_roles(hierarchy)

    effect_log_hierarchy_stats(element_count, max_depth, unique_roles)

    # ==========================================================================
    # Step 5: Search for web content
    # ==========================================================================

    effect_log_info("")
    effect_log_info("=" * 60)
    effect_log_info("STEP 5: Searching for web content")
    effect_log_info("=" * 60)

    web_areas: list[AccessibilityElementDict] = find_web_areas(hierarchy)
    effect_log_info(f"Found {len(web_areas)} AXWebArea element(s)")

    innermost_web_area: AccessibilityElementDict | None = find_innermost_web_area_with_title(hierarchy)
    if innermost_web_area:
        effect_log_info(f"Innermost web area title: {innermost_web_area.get('AXTitle', '(no title)')}")
        if innermost_web_area.get("AXURL"):
            effect_log_info(f"Innermost web area URL: {innermost_web_area.get('AXURL')}")

    # ==========================================================================
    # Step 6: Search for interactive elements
    # ==========================================================================

    effect_log_info("")
    effect_log_info("=" * 60)
    effect_log_info("STEP 6: Searching for interactive elements")
    effect_log_info("=" * 60)

    interactive_elements: list[AccessibilityElementDict] = find_interactive_elements(hierarchy)
    effect_log_info(f"Found {len(interactive_elements)} interactive element(s)")

    # Buttons
    buttons: list[AccessibilityElementDict] = find_buttons(hierarchy)
    effect_log_info(f"  - Buttons: {len(buttons)}")

    # Show first few button titles
    button_titles: list[str] = [
        btn.get("AXTitle") or btn.get("AXDescription") or "(no label)"
        for btn in buttons[:5]
    ]
    for title in button_titles:
        effect_log_info(f"      • {title}")
    if len(buttons) > 5:
        effect_log_info(f"      ... and {len(buttons) - 5} more")

    # Text areas
    text_areas: list[AccessibilityElementDict] = find_text_areas(hierarchy)
    effect_log_info(f"  - Text areas: {len(text_areas)}")

    # ==========================================================================
    # Step 7: Search for URLs
    # ==========================================================================

    effect_log_info("")
    effect_log_info("=" * 60)
    effect_log_info("STEP 7: Searching for elements with URLs")
    effect_log_info("=" * 60)

    elements_with_urls: list[AccessibilityElementDict] = find_elements_with_url(hierarchy)
    effect_log_info(f"Found {len(elements_with_urls)} element(s) with URLs")

    # Show first few URLs
    for elem in elements_with_urls[:5]:
        url: str = elem.get("AXURL", "")
        title: str = elem.get("AXTitle") or elem.get("AXDescription") or "(no title)"
        effect_log_info(f"  • {title[:40]}: {url[:60]}")
    if len(elements_with_urls) > 5:
        effect_log_info(f"  ... and {len(elements_with_urls) - 5} more")

    # ==========================================================================
    # Step 8: Search for text content
    # ==========================================================================

    effect_log_info("")
    effect_log_info("=" * 60)
    effect_log_info("STEP 8: Searching for text content")
    effect_log_info("=" * 60)

    static_text_elements: list[AccessibilityElementDict] = find_static_text(hierarchy)
    effect_log_info(f"Found {len(static_text_elements)} static text element(s)")

    # Show first few text values
    for elem in static_text_elements[:10]:
        value: str = elem.get("AXValue", "")[:80].replace("\n", "\\n")
        if value:
            effect_log_info(f"  • {value}")
    if len(static_text_elements) > 10:
        effect_log_info(f"  ... and {len(static_text_elements) - 10} more")

    # ==========================================================================
    # Step 9: Custom attribute search
    # ==========================================================================

    effect_log_info("")
    effect_log_info("=" * 60)
    effect_log_info("STEP 9: Custom attribute searches")
    effect_log_info("=" * 60)

    # Search for document articles (common in web content)
    article_results: list[SearchResult] = find_by_attribute(
        hierarchy, "AXSubrole", "AXDocumentArticle"
    )
    effect_log_info(f"Found {len(article_results)} element(s) with AXSubrole 'AXDocumentArticle'")

    for result in article_results[:3]:
        elem: AccessibilityElementDict = result["element"]
        effect_log_info(
            f"  • Path: {result['path']}, "
            f"Depth: {result['depth']}, "
            f"Title: {elem.get('AXTitle', '(no title)')[:50]}"
        )

    # Search by title (partial match)
    title_search: str = "chat"
    title_results: list[SearchResult] = find_by_title(hierarchy, title_search, partial_match=True)
    effect_log_info(f"Found {len(title_results)} element(s) with '{title_search}' in title")

    # ==========================================================================
    # Step 10: Full analysis summary
    # ==========================================================================

    effect_log_info("")
    effect_log_info("=" * 60)
    effect_log_info("STEP 10: Full analysis summary")
    effect_log_info("=" * 60)

    analysis: dict = analyze_hierarchy(hierarchy)

    effect_log_search_summary(
        analysis["web_areas_count"],
        analysis["interactive_count"],
        analysis["urls_count"],
        analysis["innermost_web_area_title"],
    )

    effect_log_info("")
    effect_log_success(f"Complete! Hierarchy saved to: {output_file_path.resolve()}")


def main() -> None:
    """Main entry point."""
    # Get target app name from command line or use default
    target_app: str = sys.argv[1] if len(sys.argv) > 1 else "atlas"
    run_example(target_app)


if __name__ == "__main__":
    main()
