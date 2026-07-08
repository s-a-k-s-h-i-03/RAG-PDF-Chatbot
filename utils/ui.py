import html

import streamlit as st

from config import APP_TITLE


def apply_app_styling() -> None:
    st.markdown(
        """
        <style>
        :root {
            --app-bg: #111315;
            --panel-bg: #17191c;
            --panel-border: #2a2e34;
            --panel-divider: #24282e;
            --text-main: #f3f4f6;
            --text-soft: #9ca3af;
            --text-faint: #6b7280;
            --message-user: #2a2f37;
            --message-assistant: #17191c;
            --chip-border: #515765;
            --chip-hover: #22262d;
            --accent: #8b5cf6;
            --viewport-offset: 3.6rem;
        }
        html, body, [data-testid="stAppViewContainer"], .stApp {
            background: var(--app-bg);
            color: var(--text-main);
        }
        .stApp {
            overflow: hidden;
        }
        .block-container {
            max-width: none;
            padding: 0 !important;
            margin: 0 !important;
        }
        [data-testid="stAppViewBlockContainer"] {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }
        [data-testid="stHeader"] {
            background: transparent !important;
            box-shadow: none !important;
            border-bottom: none !important;
            backdrop-filter: none !important;
        }
        [data-testid="stToolbar"] {
            background: transparent !important;
        }
        main {
            padding-top: 0 !important;
        }
        [data-testid="stSidebar"] {
            border-right: 1px solid #22262c;
        }
        [data-testid="stHorizontalBlock"] {
            gap: 0 !important;
            align-items: stretch !important;
        }
        [data-testid="column"] {
            min-height: calc(100vh - var(--viewport-offset));
        }
        [data-testid="column"]:first-child {
            background: #0f1114;
            border-right: 1px solid var(--panel-divider);
        }
        [data-testid="column"]:last-child {
            background: var(--panel-bg);
            padding-bottom: 1rem;
        }
        .document-empty {
            height: calc(100vh - var(--viewport-offset));
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            gap: 0.75rem;
            color: var(--text-soft);
            text-align: center;
        }
        .document-empty-icon {
            font-size: 2.2rem;
        }
        .document-empty-title {
            color: var(--text-main);
            font-size: 1.15rem;
            font-weight: 600;
        }
        .document-empty-subtitle {
            font-size: 0.95rem;
        }
        .document-viewer {
            height: calc(100vh - var(--viewport-offset));
        }
        .document-viewer iframe {
            width: 100%;
            height: calc(100vh - var(--viewport-offset));
            border: none;
            display: block;
            background: #0f1114;
        }
        .chat-header {
            padding: 1.15rem 1.4rem 0.95rem;
            border-bottom: 1px solid var(--panel-divider);
            flex-shrink: 0;
        }
        .chat-header-row {
            display: flex;
            align-items: center;
            gap: 0.9rem;
        }
        .chat-header-icon {
            width: 2rem;
            height: 2rem;
            border-radius: 999px;
            background: #222632;
            color: #c4b5fd;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
        }
        .chat-header-title {
            color: var(--text-main);
            font-size: 1rem;
            font-weight: 700;
            margin: 0;
        }
        .chat-header-subtitle {
            color: var(--text-soft);
            font-size: 0.9rem;
            margin-top: 0.18rem;
        }
        .welcome-copy {
            color: var(--text-soft);
            font-size: 0.97rem;
            line-height: 1.7;
            margin: 0 0 1rem 0;
        }
        .suggestion-row {
            display: flex;
            flex-direction: column;
            gap: 0.65rem;
            margin-bottom: 1.25rem;
        }
        .message-row {
            display: flex;
            margin-bottom: 1rem;
        }
        .message-row.user {
            justify-content: flex-end;
        }
        .message-row.assistant {
            justify-content: flex-start;
        }
        .message-bubble {
            max-width: 86%;
            padding: 0.9rem 1rem;
            border-radius: 16px;
            line-height: 1.7;
        }
        .message-bubble.user {
            background: var(--message-user);
            color: var(--text-main);
        }
        .message-bubble.assistant {
            background: transparent;
            color: var(--text-main);
            padding-left: 0;
            padding-right: 2rem;
        }
        .message-bubble p, .message-bubble li, .message-bubble td, .message-bubble th {
            color: var(--text-main);
        }
        .message-bubble code {
            color: #e5e7eb;
        }
        form[data-testid="stForm"] {
            border-top: 1px solid var(--panel-divider);
            background: #15181b;
            padding: 0.9rem 1rem 1rem;
            margin-top: 1rem;
        }
        form[data-testid="stForm"] {
            margin: 0;
        }
        form[data-testid="stForm"] .stTextInput input {
            min-height: 2.9rem;
            border: 1px solid #2f3540;
            border-radius: 999px;
            background: #101215;
            color: var(--text-main);
            box-shadow: none;
        }
        form[data-testid="stForm"] .stTextInput input::placeholder {
            color: var(--text-faint);
        }
        form[data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
            min-height: 2.9rem;
            border-radius: 999px;
            border: 1px solid #374151;
            background: #20242a;
            color: var(--text-main);
            font-weight: 600;
            box-shadow: none;
        }
        form[data-testid="stForm"] [data-testid="stFormSubmitButton"] button:hover {
            background: #282d34;
        }
        .suggestion-button [data-testid="stButton"] button {
            width: 100%;
            justify-content: flex-start;
            min-height: 2.8rem;
            border-radius: 999px;
            border: 1px solid var(--chip-border);
            background: transparent;
            color: var(--text-main);
            box-shadow: none;
        }
        .suggestion-button [data-testid="stButton"] button:hover {
            background: var(--chip-hover);
            border-color: #676d79;
            color: var(--text-main);
        }
        .main-status {
            padding: 0.8rem 1rem;
            border-bottom: 1px solid var(--panel-divider);
            background: #15181b;
            color: var(--text-soft);
        }
        @media (max-width: 900px) {
            .workspace-shell,
            .workspace-panel,
            .document-viewer,
            .document-viewer iframe,
            .document-empty {
                height: auto;
                min-height: 48vh;
            }
            .document-panel {
                border-right: none;
                border-bottom: 1px solid var(--panel-divider);
            }
            .chat-scroll {
                max-height: none;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_chat_header() -> None:
    st.markdown(
        """
        <div class="chat-header">
            <div class="chat-header-row">
                <div class="chat-header-icon">✦</div>
                <div>
                    <div class="chat-header-title">AI Assistant</div>
                    <div class="chat-header-subtitle">Ask questions about the uploaded document</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_message(role: str, content: str) -> None:
    role_class = "user" if role == "user" else "assistant"
    st.markdown(f'<div class="message-row {role_class}">', unsafe_allow_html=True)
    st.markdown(f'<div class="message-bubble {role_class}">', unsafe_allow_html=True)
    st.markdown(content)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_suggestion_buttons(suggestions: list[str]) -> str | None:
    selected = None
    st.markdown('<div class="suggestion-row">', unsafe_allow_html=True)
    for index, suggestion in enumerate(suggestions):
        st.markdown('<div class="suggestion-button">', unsafe_allow_html=True)
        if st.button(suggestion, key=f"suggestion_{index}", use_container_width=True):
            selected = suggestion
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    return selected


def render_document_placeholder() -> None:
    st.markdown(
        """
        <div class="document-empty">
            <div class="document-empty-icon">📄</div>
            <div class="document-empty-title">No document selected</div>
            <div class="document-empty-subtitle">Upload a PDF from the sidebar to begin.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_banner(message: str) -> None:
    st.markdown(
        f'<div class="main-status">{html.escape(message)}</div>',
        unsafe_allow_html=True,
    )


def render_sidebar(status_text: str) -> tuple[bool, bool, bool]:
    st.sidebar.title(APP_TITLE)
    st.sidebar.caption("Local RAG assistant powered by Ollama + FAISS")

    uploaded_file = st.sidebar.file_uploader("Upload PDF", type=["pdf"])
    if uploaded_file is not None:
        size_kb = len(uploaded_file.getvalue()) / 1024
        st.sidebar.markdown(f"**Selected file**\n\n`{uploaded_file.name}`\n\n{size_kb:.1f} KB")
    process_clicked = st.sidebar.button("Process PDF", use_container_width=True)
    clear_chat_clicked = st.sidebar.button("Clear Chat", use_container_width=True)
    reset_document_clicked = st.sidebar.button("Reset Document", use_container_width=True)

    st.sidebar.markdown("---")
    st.sidebar.write("Status")
    st.sidebar.info(status_text)

    st.sidebar.markdown("---")
    st.sidebar.write("About")
    st.sidebar.caption(
        "This assistant answers only from the uploaded PDF and runs fully locally with Ollama."
    )

    st.session_state["sidebar_uploaded_file"] = uploaded_file
    return process_clicked, clear_chat_clicked, reset_document_clicked
