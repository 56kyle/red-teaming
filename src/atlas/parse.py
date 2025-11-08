"""Module containing logic for parsing out structured data."""
import re
from pathlib import Path
from typing import Pattern

import pyperclip
from openai.types.conversations import Conversation
from openai.types.responses import ResponseInputTextParam

from openai.types.responses.response_input_item_param import Message

from atlas.constants import DATA_FOLDER


CONVERSATION_PATTERN: Pattern[str] = re.compile(
    r"You said:\n(?P<message>.*?)ChatGPT said:\n(?P<response>.*?(?=You said:|\Z))",
    re.MULTILINE | re.DOTALL
)


def parse_user_messages_from_raw_copied_text(conversation: str) -> list[Message]:
    """Splits the conversation block into a series of messages."""
    matches: list[tuple[str, str]] = CONVERSATION_PATTERN.findall(conversation)

    response_inputs: list[ResponseInputTextParam] = [
        ResponseInputTextParam(text=match[0].strip("\n"), type="input_text") for match in matches
    ]

    return [Message(content=[response_input], role="user") for response_input in response_inputs]


if __name__ == "__main__":
    path: Path = DATA_FOLDER / "agent_wiki_degrees_01.txt"
    contents: str = path.read_text(encoding="utf-8")
    messages: list[Message] = parse_user_messages_from_raw_copied_text(contents)
    # x = 9
    # print(messages[x])
    # pyperclip.copy(messages[x]["content"][0]["text"])
