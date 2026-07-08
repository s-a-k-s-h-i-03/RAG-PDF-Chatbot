import streamlit as st


WELCOME_MESSAGE = (
    "Upload a PDF, process it, and then ask questions about the document. "
    "I will answer only from the uploaded PDF."
)


def initialize_chat_state() -> None:
    st.session_state.setdefault(
        "messages",
        [{"role": "assistant", "content": WELCOME_MESSAGE}],
    )


def add_user_message(content: str) -> None:
    st.session_state.messages.append({"role": "user", "content": content})


def add_assistant_message(content: str) -> None:
    st.session_state.messages.append({"role": "assistant", "content": content})


def clear_chat() -> None:
    st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]
