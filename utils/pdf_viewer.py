import base64

import streamlit as st

from utils.ui import render_document_placeholder


def render_pdf_viewer(pdf_bytes: bytes | None) -> None:
    if not pdf_bytes:
        render_document_placeholder()
        return

    encoded_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
    pdf_display = f"""
    <div class="document-viewer">
        <iframe
            src="data:application/pdf;base64,{encoded_pdf}"
            title="PDF Viewer"
        ></iframe>
    </div>
    """
    st.markdown(pdf_display, unsafe_allow_html=True)
