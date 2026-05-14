from langchain_community.vectorstores import FAISS


def create_vector_store(chunks, embedding_model):

    vector_store = FAISS.from_texts(
        texts=chunks,
        embedding=embedding_model
    )

    return vector_store


def save_vector_store(vector_store):

    vector_store.save_local("vectorstore")


def load_vector_store(embedding_model):

    vector_store = FAISS.load_local(
        "vectorstore",
        embedding_model,
        allow_dangerous_deserialization=True
    )

    return vector_store