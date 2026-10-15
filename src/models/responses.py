import random
import time
from typing import Any, Dict, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts.chat import AIMessage, HumanMessage, SystemMessage
from langchain_ollama.llms import OllamaLLM

from src.models.rag import get_response_from_rag

# --- Constants ---
DEFAULT_SYSTEM_PROMPT = "You are a helpful AI assistant."
DEFAULT_MODEL = "gemma3:12b"
DEFAULT_GREETING = "Hi, there! Is there anything I can help you with?"

# --- Utilities ---


def stream_response_emulator() -> str:
    """
    Yields a random greeting response word by word, simulating streaming.
    """
    response = random.choice(
        [
            "Hello there! How can I assist you today?",
            "Hi, human! Is there anything I can help you with?",
            "Do you need help?",
        ]
    )
    for word in response.split():
        yield word + " "
        time.sleep(0.05)


def build_prompt_messages(messages: List[Dict[str, Any]]) -> List:
    """
    Converts a list of message dicts into LangChain chat message objects,
    including a system prompt and separating history from the latest user message.
    """
    if not messages:
        return [SystemMessage(content=DEFAULT_SYSTEM_PROMPT)]

    latest_user_message = messages[-1]["content"]
    history_messages = []
    for msg in messages[:-1]:
        if msg["role"] == "user":
            history_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            history_messages.append(AIMessage(content=msg["content"]))
        # System messages can be handled here if needed

    prompt_messages = [
        SystemMessage(content=DEFAULT_SYSTEM_PROMPT),
        *history_messages,
        HumanMessage(content=latest_user_message),
    ]
    return prompt_messages


def format_prompt(messages: List[Dict[str, Any]]) -> str:
    """
    Formats the prompt using LangChain's ChatPromptTemplate.
    """
    prompt_messages = build_prompt_messages(messages)
    prompt_value = ChatPromptTemplate(messages=prompt_messages).format_prompt()
    return prompt_value.to_string()


def clean_llm_response(response: str) -> str:
    """
    Cleans the LLM response by removing leading 'AI:' and whitespace.
    """
    return response.strip().removeprefix("AI:").strip()


# --- Main Response Generators ---


def response_generator_llm(
    messages: List[Dict[str, Any]], model: str = DEFAULT_MODEL
) -> str:
    """
    Generates a response using an LLM based on the conversation messages.
    """
    if not messages:
        return DEFAULT_GREETING

    llm = OllamaLLM(model=model)
    prompt = format_prompt(messages)
    response = llm.invoke(prompt)
    return clean_llm_response(response)


def response_generator_rag(messages: List[Dict[str, Any]]) -> str:
    """
    Generates a response using a RAG pipeline based on the conversation messages.
    """
    if not messages:
        return DEFAULT_GREETING

    prompt = format_prompt(messages)
    response = get_response_from_rag(prompt)
    return clean_llm_response(response)
