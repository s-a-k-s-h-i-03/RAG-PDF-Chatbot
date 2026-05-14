import streamlit as st

from utils.pdf_loader import extract_text_from_pdf
from utils.text_splitter import split_text_into_chunks
from utils.embeddings import get_embedding_model
from utils.vector_store import (
    create_vector_store,
    save_vector_store
)
from utils.retriever import retrieve_relevant_chunks

st.set_page_config(page_title="RAG PDF Chatbot")

st.title("RAG PDF Chatbot")

uploaded_file = st.file_uploader(
    "Upload a PDF file",
    type="pdf"
)

if uploaded_file is not None:

    st.success("PDF uploaded successfully!")

    extracted_text = extract_text_from_pdf(uploaded_file)

    chunks = split_text_into_chunks(extracted_text)

    embedding_model = get_embedding_model()

    vector_store = create_vector_store(
        chunks,
        embedding_model
    )

    save_vector_store(vector_store)

    st.success("FAISS vector store created!")

    st.subheader("Ask Questions From PDF")

    user_question = st.text_input(
        "Enter your question"
    )

    if user_question:

        retrieved_docs = retrieve_relevant_chunks(
            vector_store,
            user_question
        )

        st.subheader("Retrieved Chunks")

        for i, doc in enumerate(retrieved_docs):

            st.write(f"Chunk {i+1}")

            st.text_area(
                f"Retrieved Text {i+1}",
                doc.page_content,
                height=200
            )