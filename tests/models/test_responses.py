from types import SimpleNamespace
from unittest.mock import MagicMock

from src.config import LLMSettings
from src.models.responses import (
    SYSTEM_PROMPT,
    build_messages,
    response_generator_llm,
)

SETTINGS = LLMSettings(
    provider="ollama", base_url="http://test/v1", model="test-model", api_key="x"
)


def _chunk(text):
    return SimpleNamespace(
        choices=[SimpleNamespace(delta=SimpleNamespace(content=text))]
    )


def test_build_messages_prepends_system_prompt_and_keeps_history():
    history = [
        {"role": "user", "content": "Does niacinamide help?"},
        {"role": "assistant", "content": "Some evidence says yes."},
        {"role": "user", "content": "At what concentration?"},
    ]
    messages = build_messages(history)
    assert messages[0] == {"role": "system", "content": SYSTEM_PROMPT}
    assert messages[1:] == history


def test_response_generator_streams_and_sends_full_conversation():
    client = MagicMock()
    client.chat.completions.create.return_value = iter(
        [_chunk("Niacin"), _chunk(None), _chunk("amide")]
    )
    history = [{"role": "user", "content": "Hi"}]

    reply = "".join(response_generator_llm(history, SETTINGS, client=client))

    assert reply == "Niacinamide"
    kwargs = client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "test-model"
    assert kwargs["stream"] is True
    assert kwargs["messages"] == build_messages(history)
