"""Module containing logic for defining and interacting with ChatGPT Atlas conversations."""
from pathlib import Path
from typing import Iterable

from openai.types.conversations import ItemCreateParams
from openai.types.responses import ResponseInputItemParam

from atlas.accessibility import AXUIElementRef
from atlas.constants import DATA_FOLDER
from atlas.demo import load_planned_conversation
from atlas.interface import get_atlas_ui
from atlas.interface import _get_atlas_window
from atlas.interface import open_new_atlas_tab
from atlas.prompt import send_prompt


def play_conversation(planned_conversation: ItemCreateParams) -> None:
    """Starts a new conversation and plays through it in atlas."""
    atlas_root: AXUIElementRef = get_atlas_ui()
    atlas_window: AXUIElementRef = _get_atlas_window(atlas_root)
    open_new_atlas_tab(atlas_window)

    for item in planned_conversation["items"]:
        content: Iterable[ResponseInputItemParam] = item["content"]
        content_inputs: list[str] = [input_item["text"] for input_item in content]
        combined_input: str = "".join(content_inputs)
        send_prompt(combined_input)


if __name__ == "__main__":
    ss13_path: Path = DATA_FOLDER / "prompt_ideas" / "standard_ss13_02.json"
    planned_conversation: ItemCreateParams = load_planned_conversation(ss13_path)
    play_conversation(planned_conversation)
