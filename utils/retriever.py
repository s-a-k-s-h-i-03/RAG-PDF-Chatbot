def retrieve_relevant_chunks(vector_store, user_question):

    retrieved_docs = vector_store.similarity_search(
        user_question,
        k=3
    )

    return retrieved_docs