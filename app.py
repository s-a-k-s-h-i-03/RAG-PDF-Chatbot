import streamlit as st

from utils.pdf_loader import extract_text_from_pdf
from utils.text_splitter import split_text_into_chunks

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
        height=250
    )

    chunks = split_text_into_chunks(extracted_text)

    st.subheader("Chunk Information")

    st.write(f"Total Chunks Created: {len(chunks)}")

    if len(chunks) > 0:

        st.subheader("Sample Chunk")

        st.text_area(
            "Chunk Preview",
            chunks[0],
            height=250
        )