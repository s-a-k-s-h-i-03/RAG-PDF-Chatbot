from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS


class VectorStoreError(RuntimeError):
    """Raised when FAISS vector store operations fail."""


def create_vector_store(documents: list[Document], embedding_model) -> FAISS:
    if not documents:
        raise VectorStoreError(
            "No text chunks were created from the PDF, so the vector store could not be built."
        )

    try:
        return FAISS.from_documents(documents, embedding_model)
    except Exception as exc:
        raise VectorStoreError(
            "FAISS could not create the vector store. Check that faiss-cpu and the embedding model are installed correctly."
        ) from exc


def get_vector_store_document_count(vector_store) -> int:
    try:
        return vector_store.index.ntotal
    except Exception:
        return 0


def get_vector_store_documents(vector_store) -> list[Document]:
    try:
        docstore = getattr(vector_store, "docstore", None)
        data = getattr(docstore, "_dict", {}) if docstore is not None else {}
        return [document for document in data.values() if isinstance(document, Document)]
    except Exception:
        return []
