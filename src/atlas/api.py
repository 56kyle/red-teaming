"""Module for working with the OpenAI API in a manner convenient to the atlas package."""
import os
from pathlib import Path

from openai import Client
from openai import responses
from openai.types.conversations import Conversation


client: Client = Client(api_key=os.getenv("OPEN_AI_API_KEY_RED_TEAM"))


def get_conversation(conversation_id: str) -> Conversation:
    """Retrieves the conversation object for the given conversation ID."""
    conversation: Conversation = client.conversations.retrieve(conversation_id=conversation_id)
    print(conversation)


if __name__ == "__main__":
    # get_conversation("conversations-v3-353f8a24-ee83-4b9e-b353-cee196cf4745")
    # get_conversation("690d3239-5884-832b-8375-a0acd71b4c20")
    get_conversation("conv_690d32395884832b8375a0acd71b4c20")
    # conv = client.conversations.create()
    # print(conv)
    # get_conversation("690ee4c9-59b8-800a-bd29-87b274bc2c92")
    get_conversation("conv_690eeda4d8d481948d78e25600fdcc130622006c5dbada43")

