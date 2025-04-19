import streamlit as st

from src.views.chat import chat_view

st.header("Simple Chat App")
# st.title("Simple chat")
# st.subheader("A simple chat app using Streamlit")
# st.write("-")

chat_view()
