import streamlit as st

from src.config import LLMSettings
from src.models.responses import response_generator_llm


def chat_view(settings: LLMSettings):
    """Chat app using Streamlit"""

    # Streamlit reruns this script on every interaction, so the conversation
    # lives in session_state and is redrawn from there each time.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Only call the model when the user has just sent a message.
    if prompt := st.chat_input("Ask about an ingredient or a skin concern"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                response = st.write_stream(
                    response_generator_llm(st.session_state.messages, settings)
                )
            except Exception as error:  # surface provider errors in the UI
                st.error(f"The model call failed: {error}")
                return
        st.session_state.messages.append({"role": "assistant", "content": response})
