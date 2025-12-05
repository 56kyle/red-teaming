from __future__ import annotations

from contextlib import contextmanager
from typing import Any
from typing import Callable
from typing import List
from typing import Optional

from loguru import logger
from watchdog.events import FileSystemEvent
from watchdog.events import FileSystemEventHandler
from watchdog.observers.fsevents import FSEventsObserver

from atlas.constants import ATLAS_DATA_FOLDER


try:
    from Cocoa import NSWorkspace
    from ApplicationServices import (
        AXUIElementCopyAttributeValue,
        AXUIElementCreateApplication,
        kAXChildrenAttribute,
        kAXRoleAttribute,
        kAXTitleAttribute,
        kAXValueAttribute,
        kAXWindowsAttribute,
    )
except Exception as import_error:
    raise RuntimeError(
        "PyObjC must be installed and this module must run on macOS."
    ) from import_error


def ax_get_value(element: Any, attribute: str) -> Optional[Any]:
    """Return an AX attribute value or None."""
    try:
        return AXUIElementCopyAttributeValue(element, attribute, None)
    except Exception as e:
        logger.warning(e)
        return None


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


def get_atlas_accessibility_root() -> Any:
    """Return the AX root for the ChatGPT Atlas app and ensure it is running/setup."""
    atlas_root: Optional[Any] = find_atlas_accessibility_root()
    if not atlas_root:
        raise RuntimeError("ChatGPT Atlas application is not running")
    if not ATLAS_DATA_FOLDER.exists():
        raise FileNotFoundError(f"Missing expected Atlas data directory: {ATLAS_DATA_FOLDER}")
    return atlas_root


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
    results: List[Any] = []
    stack: List[Any] = ax_get_children(root_window)

    while stack:
        node: Any = stack.pop()
        role: Optional[str] = ax_get_role(node)
        if role == "AXWebArea":
            results.append(node)
        stack.extend(ax_get_children(node))

    return results


class AtlasBrowserState:
    IDLE: str = "idle"
    GENERATING: str = "generating"
    AGENT_RUNNING: str = "agent_running"


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

    def on_any_event(self, event: FileSystemEvent) -> None:
        logger.info(event)
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
    if not ATLAS_DATA_FOLDER.exists():
        logger.error(f"Missing expected Atlas data directory: {ATLAS_DATA_FOLDER}")
        return

    handler: AtlasContentEventHandler = AtlasContentEventHandler(atlas_root=atlas_root, on_change=on_state_change)

    with atlas_file_observer(handler) as observer:
        while True:
            pass

@contextmanager
def atlas_file_observer(handler: AtlasContentEventHandler):
    """Yield a running FSEventsObserver and ensure proper cleanup."""
    observer: FSEventsObserver = FSEventsObserver()
    try:
        observer.schedule(handler, str(ATLAS_DATA_FOLDER), recursive=True)
        observer.start()
        logger.info("Atlas state observer started")
        yield observer
    finally:
        observer.stop()
        observer.join()
        logger.info("Atlas state observer stopped")


def handle_state_change(state: str) -> None:
    """Callback that logs any changes to the atlas browser's state."""
    logger.info(f"Atlas browser state changed: {state}")


if __name__ == "__main__":
    atlas_root: Any = find_atlas_accessibility_root()
    print(dir(atlas_root))
    # monitor_atlas_state(handle_state_change)

