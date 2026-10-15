"""The model layer: one client for any OpenAI-compatible provider."""

from typing import Dict, Iterator, List, Optional

from openai import OpenAI

from src.config import LLMSettings

Message = Dict[str, str]


def get_client(settings: LLMSettings) -> OpenAI:
    return OpenAI(base_url=settings.base_url, api_key=settings.api_key)


def stream_chat(
    messages: List[Message],
    settings: LLMSettings,
    client: Optional[OpenAI] = None,
) -> Iterator[str]:
    """Send the conversation to the model and yield the reply as it is generated.

    The model is stateless: `messages` must hold the whole conversation every time.
    """
    client = client or get_client(settings)
    stream = client.chat.completions.create(
        model=settings.model,
        messages=messages,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
