import random
import time

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.prompts.chat import AIMessage, HumanMessage, SystemMessage
from langchain_ollama.llms import OllamaLLM


# Streamed response emulator
def response_generator():
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


# Define the template ONCE (e.g., outside the function or memoized)
chat_template = ChatPromptTemplate.from_messages(
    [
        SystemMessage(
            content="You are a helpful AI assistant."
        ),  # Fixed system message
        MessagesPlaceholder(variable_name="history"),  # Placeholder for chat history
        HumanMessage(content="{user_input}"),  # Placeholder for the latest user input
    ]
)


def response_generator_llm(messages):
    llm = OllamaLLM(model="gemma3:12b")  # Or initialize outside if preferred

    if not messages:
        return "Hi, there! Is there anything I can help you with?"

    # Separate the latest user message from the history
    latest_user_message = messages[-1]["content"]
    history_messages = []
    for msg in messages[:-1]:  # Exclude the latest user message
        if msg["role"] == "user":
            history_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            history_messages.append(AIMessage(content=msg["content"]))
        # You might handle system messages differently or assume they are fixed

    prompt_messages = [
        SystemMessage(content="You are a helpful AI assistant."),
        *history_messages,
        HumanMessage(content=latest_user_message),
    ]

    prompt_value = ChatPromptTemplate(messages=prompt_messages).format_prompt()

    response = llm.invoke(prompt_value.to_string())
    clean_response = response.lstrip("AI:").strip()
    return clean_response
