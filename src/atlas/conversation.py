"""Module containing logic for defining and interacting with ChatGPT Atlas conversations."""
import json
from pathlib import Path
from typing import Iterable
from typing import Optional

from loguru import logger
from openai.types.conversations import ItemCreateParams
from openai.types.responses import ResponseInputItemParam
from openai.types.responses.response_input_item_param import Message

from atlas._typing import PlannedConversation
from atlas.accessibility import AXUIElementRef
from atlas.constants import DATA_FOLDER
from atlas.interface import get_atlas_ui
from atlas.interface import _get_atlas_window
from atlas.interface import open_new_atlas_tab
from atlas.parse import parse_user_messages_from_raw_copied_text
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
        response: str = send_prompt(combined_input)
        logger.debug(response)


def get_user_messages_from_conversation(path: Path) -> Optional[list[ResponseInputItemParam]]:
    """Loads all user messages from a conversation."""
    logger.info("Loading planned conversation from file")
    params: ItemCreateParams = load_planned_conversation(path=path)
    items: list[ResponseInputItemParam] = list(params.get("items", []))

    if not items:
        logger.warning("No conversation items found in file")
        return None

    user_messages: list[ResponseInputItemParam] = _filter_user_messages(items)
    return user_messages


def _filter_user_messages(items: list[ResponseInputItemParam]) -> list[ResponseInputItemParam]:
    """Filter items to only include messages with role='user'."""
    user_messages: list[ResponseInputItemParam] = [item for item in items if item.get("role") == "user"]
    logger.debug(f"Filtered {len(items)} items to {len(user_messages)} user messages")
    return user_messages


def save_planned_conversation(path: Path, messages: list[Message]) -> None:
    """Save a planned conversation."""
    params: ItemCreateParams = ItemCreateParams(items=messages)
    content: str = json.dumps(params, indent=2)
    PlannedConversation.validate_json(content)
    path.write_text(data=content)


def load_planned_conversation(path: Path) -> ItemCreateParams:
    """Load a planned conversation."""
    content: str = path.read_text()
    params: ItemCreateParams = PlannedConversation.validate_json(content)
    return params


def transfer_raw_copied_to_planned_conversation(path: Path) -> None:
    """Parses raw copied text at the provided path into a planned conversation."""
    contents: str = path.read_text(encoding="utf-8")
    messages: list[Message] = parse_user_messages_from_raw_copied_text(conversation=contents)

    output_path: Path = path.with_suffix(".json")
    save_planned_conversation(path=output_path, messages=messages)


if __name__ == "__main__":
    ss13_path: Path = DATA_FOLDER / "prompt_ideas" / "standard_ss13_02.json"
    planned_conversation: ItemCreateParams = load_planned_conversation(ss13_path)
    play_conversation(planned_conversation)
