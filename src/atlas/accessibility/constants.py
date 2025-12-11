"""Constants and attribute profiles for the accessibility package."""

from __future__ import annotations


# =============================================================================
# ATTRIBUTE GROUPS
# =============================================================================


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

STATE_ATTRIBUTES: tuple[str, ...] = (
    "AXEnabled",
    "AXFocused",
    "AXSelected",
    "AXExpanded",
    "AXRequired",
    "AXElementBusy",
)

EXTENDED_TEXT_ATTRIBUTES: tuple[str, ...] = (
    "AXValueDescription",
    "AXHelp",
    "AXPlaceholderValue",
)

WEB_ATTRIBUTES: tuple[str, ...] = (
    "AXURL",
    "AXDOMIdentifier",
    "AXDOMClassList",
    "AXVisited",
)

LINK_ATTRIBUTES: tuple[str, ...] = (
    "AXURL",
    "AXVisited",
)

ALL_STANDARD_ATTRIBUTES: tuple[str, ...] = (
    CORE_ATTRIBUTES + STATE_ATTRIBUTES + EXTENDED_TEXT_ATTRIBUTES + WEB_ATTRIBUTES
)

DEFAULT_ATTRIBUTES: tuple[str, ...] = CORE_ATTRIBUTES + STATE_ATTRIBUTES

# =============================================================================
# SPECIAL ATTRIBUTE SETS
# =============================================================================


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

INTERACTIVE_ROLES: frozenset[str] = frozenset(
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

# =============================================================================
# ROLE CONSTANTS
# =============================================================================


AXROLE_WEB_AREA: str = "AXWebArea"
AXROLE_APPLICATION: str = "AXApplication"
AXROLE_WINDOW: str = "AXWindow"
AXROLE_BUTTON: str = "AXButton"
AXROLE_TEXT_FIELD: str = "AXTextField"
AXROLE_TEXT_AREA: str = "AXTextArea"
AXROLE_STATIC_TEXT: str = "AXStaticText"
AXROLE_LINK: str = "AXLink"
AXROLE_GROUP: str = "AXGroup"
AXROLE_LIST: str = "AXList"
AXROLE_SCROLL_AREA: str = "AXScrollArea"


# =============================================================================
# ATTRIBUTE PROFILES
# =============================================================================


class AttributeProfile:
    """Predefined attribute collection profiles for different use cases.

    Profiles provide convenient groupings of attributes for common scenarios:
    - MINIMAL: Just identification (role, subrole, title, identifier)
    - DEFAULT: Core attributes plus state information
    - WEB_FOCUSED: Includes web-specific attributes like URLs and DOM info
    - FULL: All standard attributes
    """

    MINIMAL: tuple[str, ...] = (
        "AXRole",
        "AXSubrole",
        "AXTitle",
        "AXIdentifier",
    )

    DEFAULT: tuple[str, ...] = DEFAULT_ATTRIBUTES

    WEB_FOCUSED: tuple[str, ...] = CORE_ATTRIBUTES + STATE_ATTRIBUTES + WEB_ATTRIBUTES

    FULL: tuple[str, ...] = ALL_STANDARD_ATTRIBUTES
