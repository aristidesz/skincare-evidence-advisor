from typing import Dict, Iterator, List, Optional

from openai import OpenAI

from src.config import LLMSettings
from src.models.llm import Message, stream_chat

SYSTEM_PROMPT = (
    "You are an evidence-based skincare advisor. Explain what the clinical "
    "evidence says about skincare ingredients, say how strong that evidence is, "
    "and avoid marketing language. You give general educational information, "
    "not medical advice: for symptoms such as a changing mole, infection or "
    "severe acne, recommend seeing a GP or dermatologist."
)


def build_messages(history: List[Dict[str, str]]) -> List[Message]:
    """Prepend the system prompt to the chat history kept by the app."""
    turns = [
        {"role": m["role"], "content": m["content"]}
        for m in history
        if m["role"] in ("user", "assistant")
    ]
    return [{"role": "system", "content": SYSTEM_PROMPT}, *turns]


def response_generator_llm(
    history: List[Dict[str, str]],
    settings: LLMSettings,
    client: Optional[OpenAI] = None,
) -> Iterator[str]:
    """Stream the assistant's reply to the conversation so far."""
    return stream_chat(build_messages(history), settings, client=client)
