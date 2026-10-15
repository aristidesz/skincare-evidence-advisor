import streamlit as st

from src.config import load_llm_settings
from src.views.chat import chat_view

st.header("Simple Chat App")

try:
    settings = load_llm_settings()
except ValueError as error:
    st.error(str(error))
    st.stop()

st.caption(f"Model: {settings.model} via {settings.provider}")

chat_view(settings)
