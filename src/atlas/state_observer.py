from __future__ import annotations
from typing import Optional, List, Callable, Any
from pathlib import Path

from Cocoa import NSWorkspace
from Quartz import (
    AXUIElementCreateApplication,
    AXUIElementCopyAttributeValue,
    kAXWindowsAttribute,
    kAXChildrenAttribute,
    kAXRoleAttribute,
    kAXTitleAttribute,
    kAXValueAttribute,
)

from ctypes import byref
from loguru import logger
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


def ax_get_value(element: Any, attribute: str) -> Optional[Any]:
    """Return an AX attribute value or None."""
    result: Any = None
    status: int = AXUIElementCopyAttributeValue(element, attribute, byref(result))
    return result if status == 0 else None


def ax_get_children(element: Any) -> List[Any]:
    """Return a list of an AX element's children."""
    raw_children: Optional[Any] = ax_get_value(element, kAXChildrenAttribute)
    return list(raw_children) if raw_children else []


def ax_get_role(element: Any) -> Optional[str]:
    """Return the accessibility role of an AX element."""
    role: Optional[Any] = ax_get_value(element, kAXRoleAttribute)
    return str(role) if role else None


def ax_get_title(element: Any) -> Optional[str]:
    """Return the accessibility title of an AX element."""
    title: Optional[Any] = ax_get_value(element, kAXTitleAttribute)
    return str(title) if title else None


def ax_get_text(element: Any) -> Optional[str]:
    """Return the accessibility text value of an AX element."""
    value: Optional[Any] = ax_get_value(element, kAXValueAttribute)
    return str(value) if value else None


def find_atlas_accessibility_root() -> Optional[Any]:
    """Return the AX root for the ChatGPT Atlas app if running."""
    workspace = NSWorkspace.sharedWorkspace()
    apps = workspace.runningApplications()
    for app in apps:
        name: str = str(app.localizedName())
        if "ChatGPT" in name:
            return AXUIElementCreateApplication(app.processIdentifier())
    return None


def collect_attribute_values(root: Any, extractor: Callable[[Any], Optional[str]]) -> List[str]:
    """Return a flattened list of specific attribute values from an AX subtree."""
    stack: List[Any] = [root]
    results: List[str] = []
    while stack:
        node: Any = stack.pop()
        extracted: Optional[str] = extractor(node)
        if extracted:
            results.append(extracted)
        stack.extend(ax_get_children(node))
    return results


def find_webview_nodes(root_window: Any) -> List[Any]:
    """Return a list of AXWebArea nodes inside a window."""
    stack: List[Any] = ax_get_children(root_window)
    results: List[Any] = []
    while stack:
        node: Any = stack.pop()
        role: Optional[str] = ax_get_role(node)
        if role == "AXWebArea":
            results.append(node)
        stack.extend(ax_get_children(node))
    return results


class AtlasBrowserState:
    IDLE = "idle"
    GENERATING = "generating"
    AGENT_RUNNING = "agent_running"


def derive_atlas_state(text_nodes: List[str], button_labels: List[str]) -> str:
    """Return a classified state derived from webview text and labels."""
    if any("Stop" in label for label in button_labels):
        return AtlasBrowserState.GENERATING
    agent_tokens: List[str] = ["agent", "working", "performing task"]
    if any(keyword in text.lower() for text in text_nodes for keyword in agent_tokens):
        return AtlasBrowserState.AGENT_RUNNING
    return AtlasBrowserState.IDLE


def inspect_atlas_state(root_app: Any) -> Optional[str]:
    """Return the current Atlas state by evaluating the primary webview."""
    windows: Optional[Any] = ax_get_value(root_app, kAXWindowsAttribute)
    if not windows:
        return None
    root_window: Any = windows[0]
    webviews: List[Any] = find_webview_nodes(root_window)
    if not webviews:
        return None
    webview: Any = webviews[0]
    text_nodes: List[str] = collect_attribute_values(webview, ax_get_text)
    button_labels: List[str] = collect_attribute_values(webview, ax_get_title)
    return derive_atlas_state(text_nodes, button_labels)


class AtlasContentEventHandler(FileSystemEventHandler):
    """Dispatch state change events based on filesystem updates."""
    def __init__(self, atlas_root: Any, on_change: Callable[[str], None]) -> None:
        super().__init__()
        self._atlas_root: Any = atlas_root
        self._on_change: Callable[[str], None] = on_change
        self._last_state: Optional[str] = None

    def on_any_event(self, event) -> None:
        new_state: Optional[str] = inspect_atlas_state(self._atlas_root)
        if new_state and new_state != self._last_state:
            self._last_state = new_state
            self._on_change(new_state)


def monitor_atlas_state(on_state_change: Callable[[str], None]) -> None:
    """Monitor Atlas browser state and dispatch changes on update events."""
    atlas_root: Optional[Any] = find_atlas_accessibility_root()
    if not atlas_root:
        logger.error("ChatGPT Atlas application is not running")
        return
    atlas_data_root: Path = Path("~/Library/Application Support/com.openai.chatgpt").expanduser()
    if not atlas_data_root.exists():
        logger.error(f"Missing expected Atlas data directory: {atlas_data_root}")
        return
    handler: AtlasContentEventHandler = AtlasContentEventHandler(atlas_root, on_state_change)
    observer: Observer = Observer()
    observer.schedule(handler, str(atlas_data_root), recursive=True)
    logger.info("Atlas state observer started")
    observer.start()
    observer.join()


def handle_state_change(state: str) -> None:
    """Small callback function to document state changes."""
    logger.info(f"Atlas browser state changed: {state}")


if __name__ == "__main__":
    monitor_atlas_state(handle_state_change)
