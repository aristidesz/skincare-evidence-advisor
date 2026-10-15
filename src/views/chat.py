import streamlit as st

from src.models.responses import response_generator_llm, response_generator_rag


def chat_view():
    """Chat app using Streamlit"""

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("What is up?"):
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            # response = st.write_stream(response_generator())
            flag_rag = True
            if flag_rag:
                response = response_generator_rag(st.session_state.messages)
            else:
                response = response_generator_llm(st.session_state.messages)
            st.write(response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
