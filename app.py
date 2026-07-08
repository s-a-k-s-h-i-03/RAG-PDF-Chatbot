import hashlib

import streamlit as st

from config import APP_ICON, APP_TITLE
from services.rag_pipeline import RAGPipeline
from utils.chat_manager import (
    add_assistant_message,
    add_user_message,
    clear_chat,
    initialize_chat_state,
)
from utils.embeddings import EmbeddingSetupError, check_embedding_model_available, get_embedding_model
from utils.llm import get_llm_status
from utils.pdf_loader import PDFProcessingError
from utils.pdf_viewer import render_pdf_viewer
from utils.retriever import RetrievalError
from utils.ui import (
    apply_app_styling,
    render_chat_header,
    render_message,
    render_sidebar,
    render_status_banner,
    render_suggestion_buttons,
)
from utils.vector_store import VectorStoreError


def initialize_app_state() -> None:
    defaults = {
        "processed_document": None,
        "processing_status": "Waiting for a PDF.",
        "is_processing": False,
        "is_generating": False,
        "last_error": None,
        "pending_question": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_document() -> None:
    st.session_state.processed_document = None
    st.session_state.processing_status = "Document reset."
    st.session_state.is_processing = False
    st.session_state.is_generating = False
    st.session_state.last_error = None
    st.session_state.pending_question = None
    clear_chat()


def get_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def get_suggested_questions() -> list[str]:
    return [
        "What is this document about?",
        "Summarize this PDF",
        "Explain the key concepts",
    ]


def build_status_text(ollama_status, embedding_status) -> str:
    if not embedding_status.model_available:
        return "Embedding model cache missing."
    if not ollama_status.installed:
        return "Ollama is not installed."
    if not ollama_status.running:
        return "Ollama service is not running."
    if not ollama_status.model_available:
        return "No supported local Ollama model detected."
    if not ollama_status.llm_ready:
        return "Ollama model check failed."
    if st.session_state.processed_document:
        return f"Ready with {st.session_state.processed_document.file_name}"
    return "Ready to process a PDF."


@st.cache_resource(show_spinner=False)
def get_pipeline() -> RAGPipeline:
    embedding_model = get_embedding_model()
    return RAGPipeline(embedding_model)


def process_uploaded_document(uploaded_file) -> None:
    if uploaded_file is None:
        st.session_state.last_error = "Please upload a PDF before processing."
        return

    pdf_bytes = uploaded_file.getvalue()
    file_hash = get_file_hash(pdf_bytes)
    current_document = st.session_state.processed_document

    if current_document and current_document.file_hash == file_hash:
        st.session_state.processing_status = "This PDF is already processed."
        return

    st.session_state.is_processing = True
    st.session_state.last_error = None
    st.session_state.processing_status = "Processing PDF..."

    try:
        with st.spinner("Processing your PDF..."):
            processed_document = get_pipeline().process_pdf(
                pdf_bytes=pdf_bytes,
                file_name=uploaded_file.name,
                file_hash=file_hash,
            )
        st.session_state.processed_document = processed_document
        st.session_state.pending_question = None
        clear_chat()
        st.session_state.processing_status = "PDF processed successfully."
    except (PDFProcessingError, EmbeddingSetupError, VectorStoreError) as exc:
        st.session_state.last_error = str(exc)
        st.session_state.processing_status = "Processing failed."
    except Exception:
        st.session_state.last_error = "An unexpected error occurred while processing the PDF."
        st.session_state.processing_status = "Processing failed."
    finally:
        st.session_state.is_processing = False


def format_sources(pages: list[int]) -> str:
    if not pages:
        return "Source: Page not available"
    labels = ", ".join(f"Page {page}" for page in pages)
    return f"Source: {labels}"


def handle_question(question: str) -> None:
    processed_document = st.session_state.processed_document
    if processed_document is None:
        st.session_state.last_error = "Please process a PDF before asking questions."
        return

    st.session_state.is_generating = True
    st.session_state.last_error = None
    add_user_message(question)

    try:
        retrieved_docs = get_pipeline().retrieve(processed_document.vector_store, question)
        stream, pages = get_pipeline().generate_answer(question, retrieved_docs)

        answer_parts: list[str] = []
        for token in stream:
            answer_parts.append(token)

        answer_text = "".join(answer_parts).strip()
        if not answer_text:
            answer_text = "I could not find this information in the uploaded PDF."

        final_answer = f"{answer_text}\n\n{format_sources(pages)}"
        add_assistant_message(final_answer)
    except RetrievalError as exc:
        add_assistant_message(str(exc))
    except Exception as exc:
        message = str(exc) or "The assistant could not generate an answer right now."
        add_assistant_message(message)
    finally:
        st.session_state.is_generating = False


st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")
apply_app_styling()
initialize_app_state()
initialize_chat_state()

embedding_status = check_embedding_model_available()
ollama_status = get_llm_status()

status_text = build_status_text(ollama_status, embedding_status)
process_clicked, clear_chat_clicked, reset_document_clicked = render_sidebar(status_text)
uploaded_file = st.session_state.get("sidebar_uploaded_file")
processed_document = st.session_state.processed_document

if not embedding_status.model_available:
    st.warning(embedding_status.message)
if not ollama_status.installed:
    st.warning(ollama_status.message)
elif not ollama_status.running:
    st.warning(ollama_status.message)
elif not ollama_status.model_available or not ollama_status.llm_ready:
    st.warning(ollama_status.message)

if clear_chat_clicked:
    clear_chat()
    st.session_state.pending_question = None

if reset_document_clicked:
    reset_document()

if uploaded_file and process_clicked:
    process_uploaded_document(uploaded_file)
    st.rerun()

if st.session_state.last_error:
    st.error(st.session_state.last_error)

main_left, main_right = st.columns([52, 48], gap="small")

with main_left:
    render_pdf_viewer(processed_document.pdf_bytes if processed_document else None)

submitted = False
question = ""
selected_question = None

with main_right:
    render_chat_header()

    if processed_document is not None:
        render_status_banner(f"Loaded: {processed_document.file_name}")
    else:
        render_status_banner("Upload and process a PDF from the sidebar to start chatting.")

    if len(st.session_state.messages) <= 1:
        render_message(
            "assistant",
            (
                "I can answer questions only from the uploaded PDF. "
                "Process a document and then ask for summaries, explanations, key points, or topic-wise details."
            ),
        )
        if processed_document is not None:
            selected_question = render_suggestion_buttons(get_suggested_questions())

    messages_to_render = st.session_state.messages if len(st.session_state.messages) > 1 else []
    for message in messages_to_render:
        render_message(message["role"], message["content"])

    chat_disabled = (
        processed_document is None
        or st.session_state.is_processing
        or st.session_state.is_generating
        or not embedding_status.model_available
        or not ollama_status.llm_ready
    )

    with st.form("chat_form", clear_on_submit=True):
        input_col, send_col = st.columns([82, 18], gap="small")
        with input_col:
            question = st.text_input(
                "Ask anything about this PDF",
                placeholder="Ask anything about this PDF...",
                disabled=chat_disabled,
                label_visibility="collapsed",
            )
        with send_col:
            submitted = st.form_submit_button(
                "Send",
                use_container_width=True,
                disabled=chat_disabled,
            )

if selected_question and not chat_disabled:
    st.session_state.pending_question = selected_question

if submitted and question:
    handle_question(question)
    st.rerun()

if st.session_state.pending_question and not st.session_state.is_generating:
    pending = st.session_state.pending_question
    st.session_state.pending_question = None
    handle_question(pending)
    st.rerun()
