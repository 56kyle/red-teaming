"""Type definitions for the accessibility package."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import TypedDict


# Type alias for the opaque AXUIElement reference from macOS
AXUIElementRef = Any


class PointDict(TypedDict):
    """A 2D point with x and y coordinates."""
    x: float
    y: float


class SizeDict(TypedDict):
    """A 2D size with width and height."""
    width: float
    height: float


class RangeDict(TypedDict):
    """A range with location and length (maps to CFRange)."""
    location: int
    length: int


class BoundsDict(TypedDict):
    """Screen bounds consisting of position and size."""
    position: PointDict
    size: SizeDict


class ApplicationInfo(TypedDict):
    """Information about a running application."""
    name: str
    process_id: int
    bundle_identifier: str | None


class AccessibilityElementDict(TypedDict, total=False):
    """Dictionary representation of an accessibility element.

    All fields are optional (total=False) since different elements
    have different available attributes.
    """
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
    position: PointDict
    size: SizeDict

    # Hierarchy
    children: list[AccessibilityElementDict]
    windows: list[AccessibilityElementDict]

    # Meta
    truncated: bool
    cycle_detected: bool
    available_attributes: list[str]
    available_parameterized_attributes: list[str]


class SearchResult(TypedDict):
    """Result of a hierarchy search operation."""
    element: AccessibilityElementDict
    path: list[int]
    depth: int


@dataclass(frozen=True)
class ConversionConfig:
    """Immutable configuration for hierarchy conversion.

    Attributes:
        maximum_depth: Maximum depth to traverse in the hierarchy
        include_available_attributes: Include list of all available attributes
        include_parameterized_attributes: Include list of parameterized attributes
        attributes_to_capture: Tuple of attribute names to capture
        include_windows_as_children: Merge windows into children list
    """
    maximum_depth: int = 10
    include_available_attributes: bool = False
    include_parameterized_attributes: bool = False
    attributes_to_capture: tuple[str, ...] = (
        "AXRole",
        "AXSubrole",
        "AXRoleDescription",
        "AXIdentifier",
        "AXTitle",
        "AXDescription",
        "AXLabel",
        "AXValue",
        "AXEnabled",
        "AXFocused",
        "AXSelected",
        "AXExpanded",
        "AXRequired",
        "AXElementBusy",
    )
    include_windows_as_children: bool = True
