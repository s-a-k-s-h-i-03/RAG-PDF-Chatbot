import streamlit as st

from utils.pdf_loader import extract_text_from_pdf
from utils.text_splitter import split_text_into_chunks
from utils.embeddings import get_embedding_model
from utils.vector_store import (
    create_vector_store,
    save_vector_store
)

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
        height=200
    )

    chunks = split_text_into_chunks(extracted_text)

    st.subheader("Chunk Information")

    st.write(f"Total Chunks Created: {len(chunks)}")

    embedding_model = get_embedding_model()

    st.info("Creating embeddings and FAISS vector store...")

    vector_store = create_vector_store(
        chunks,
        embedding_model
    )

    save_vector_store(vector_store)

    st.success("FAISS vector store created successfully!")

    st.write("Vector database saved locally.")