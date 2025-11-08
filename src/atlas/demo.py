"""Module containing logic for demoing a red teaming example."""
import json
from pathlib import Path

from openai.types.conversations import ItemCreateParams
from openai.types.responses.response_input_item_param import Message
from pydantic import TypeAdapter

from atlas.constants import DATA_FOLDER
from atlas.parse import parse_user_messages_from_raw_copied_text


PlannedConversation: TypeAdapter[ItemCreateParams] = TypeAdapter(ItemCreateParams)


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
    path: Path = DATA_FOLDER / "agent_wiki_degrees_01.txt"
    transfer_raw_copied_to_planned_conversation(path)
