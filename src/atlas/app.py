"""Module containing logic for interacting with Atlas as an application."""
from __future__ import annotations

import subprocess
import time
from typing import Any
from loguru import logger

from atlas.accessibility import ApplicationInfo
from atlas.constants import ATLAS_APP_EXECUTABLE_PATH
from atlas.constants import ATLAS_APP_NAME


try:
    from Cocoa import (
        NSApplicationActivationPolicyRegular,
        NSWorkspace,
    )
except ImportError as import_error:
    logger.error(f"Failed to import required macOS frameworks: {import_error}")
    raise


def get_or_create_atlas_application(timeout: float = 5) -> ApplicationInfo:
    """Get or create an Atlas application."""
    atlas_application: ApplicationInfo | None = _find_atlas_with_regular_activation_policy()
    if atlas_application is None:
        _launch_atlas()
        return _wait_for_atlas(timeout=timeout)
    return atlas_application


def _launch_atlas() -> subprocess.Popen[bytes]:
    """Launch the Atlas browser executable and verify startup stabilization."""
    logger.info(f"Launching browser from {ATLAS_APP_EXECUTABLE_PATH}")

    if not ATLAS_APP_EXECUTABLE_PATH.exists():
        msg: str = f"Atlas executable not found at {ATLAS_APP_EXECUTABLE_PATH}"
        raise FileNotFoundError(msg)

    process: subprocess.Popen[bytes] = subprocess.Popen(
        [str(ATLAS_APP_EXECUTABLE_PATH)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    logger.info(f"Browser launched with PID {process.pid}")
    return process


def _wait_for_atlas(timeout: float) -> ApplicationInfo:
    """Waits until the atlas application is ready."""
    start_time: float = time.time()
    while time.time() - start_time < timeout:
        result: ApplicationInfo | None = _find_atlas_with_regular_activation_policy()
        if result is not None:
            return result
    raise TimeoutError(f"Timed out waiting {timeout} seconds for atlas to launch.")


def _find_atlas_with_regular_activation_policy() -> ApplicationInfo | None:
    """Returns the Atlas application that has a regular activation policy if present."""
    running_applications: list[ApplicationInfo] = _get_running_applications_with_regular_activation_policy()
    for application in running_applications:
        if application["bundle_identifier"] == ATLAS_APP_NAME:
            return application
    return None


def _get_running_applications_with_regular_activation_policy() -> list[ApplicationInfo]:
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


if __name__ == "__main__":
    app: ApplicationInfo = get_or_create_atlas_application()
