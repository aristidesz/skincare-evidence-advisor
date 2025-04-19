import random
import time

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


def response_generator_llm():
    # Initialize the Ollama model
    llm = OllamaLLM(model="gemma3:12b")

    # Format the input for the Ollama model
    prompt = "Randomly generated response:"

    # Generate a response using the Ollama model
    response = llm.invoke(prompt)
    return response
