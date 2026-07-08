import streamlit as st

from utils.llm import get_ollama_status


def run_startup_verification(preferred_model: str = "phi3"):
    st.write("Checking Ollama...")
    status = get_ollama_status(preferred_model)

    st.write("Checking model...")
    if status.model_available:
        st.write("Model found.")

    return status


def render_health_panel(status) -> None:
    yes = "\u2705"
    no = "\u274c"

    st.sidebar.subheader("System Health")
    st.sidebar.write(f"Ollama Installed {yes if status.installed else no}")
    st.sidebar.write(f"Ollama Running {yes if status.running else no}")
    st.sidebar.write(f"Model Available {yes if status.model_available else no}")
    st.sidebar.write(f"Selected Model: {status.selected_model or status.requested_model}")
    st.sidebar.write(f"Model Detection Status: {status.detection_status}")
    st.sidebar.write(f"LLM Ready {yes if status.llm_ready else no}")

    if not status.llm_ready:
        st.sidebar.caption(status.llm_test_message)

    st.sidebar.caption("Detected Models:")
    if status.available_models:
        for model_name in status.available_models:
            st.sidebar.write(f"- {model_name}")
    else:
        st.sidebar.write("none")
