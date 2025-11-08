"""Module containing custom types used throughout the atlas package."""
from openai.types.conversations import ItemCreateParams
from pydantic import TypeAdapter


PlannedConversation: TypeAdapter[ItemCreateParams] = TypeAdapter(ItemCreateParams)
