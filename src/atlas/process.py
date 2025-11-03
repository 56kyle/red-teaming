"""Module containing logic for working with the ChatGPT Atlas process."""
from typing import Optional

import psutil


ATLAS_PROCESS_NAME: str = "ChatGPT Atlas"


def get_atlas_process() -> psutil.Process:
    """Returns the process with the name 'ChatGPT Atlas'."""
    process: Optional[psutil.Process] = find_process_by_name(ATLAS_PROCESS_NAME)
    if process is None:
        raise ValueError(f"Process with name '{ATLAS_PROCESS_NAME}' not found.")
    return process


def find_process_by_name(name: str) -> Optional[psutil.Process]:
    """Find a process by its name."""
    for proc in psutil.process_iter():
        if proc.name() == name:
            return proc
    return None


if __name__ == "__main__":
    print(get_atlas_process())
