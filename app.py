import streamlit as st
from utils.pdf_loader import extract_text_from_pdf

st.set_page_config(page_title="RAG PDF Chatbot")

st.title("RAG PDF Chatbot")

uploaded_file = st.file_uploader(
    "Upload a PDF file",
    type="pdf"
)

if uploaded_file is not None:

    st.success("PDF uploaded successfully!")

    extracted_text = extract_text_from_pdf(uploaded_file)

    st.subheader("Extracted Text Preview")

    st.text_area(
        "PDF Content",
        extracted_text[:3000],
        height=300
    )