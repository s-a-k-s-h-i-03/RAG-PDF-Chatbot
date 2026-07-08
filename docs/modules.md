# Modules Reference

## app.py
Main Streamlit entry point.

### Functions
- `initialize_app_state()`: seeds UI state keys.
- `reset_document()`: clears processed document state and chat history.
- `get_file_hash(file_bytes)`: returns SHA-256 hash.
- `get_suggested_questions()`: returns three static suggestions.
- `build_status_text(ollama_status, embedding_status)`: computes sidebar status text.
- `get_pipeline()`: cached `RAGPipeline` factory.
- `process_uploaded_document(uploaded_file)`: processes the uploaded PDF and updates session state.
- `format_sources(pages)`: converts page numbers into a source string.
- `handle_question(question)`: retrieves documents, generates an answer, and appends it to chat history.

## config.py
Constants only.

### Current key constants
- `DEFAULT_MODEL = "tinyllama"`
- `FALLBACK_MODELS = ["tinyllama", "phi3", "gemma:2b", "mistral"]`
- `EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"`
- `EMBEDDING_FALLBACK_MODELS = ["BAAI/bge-small-en-v1.5", "sentence-transformers/all-MiniLM-L6-v2"]`
- `CHUNK_SIZE = 600`
- `CHUNK_OVERLAP = 150`
- `RETRIEVAL_TOP_K = 8`
- `RETRIEVAL_FETCH_K = 20`
- `RETRIEVAL_LAMBDA_MULT = 0.7`
- `MAX_CONTEXT_CHARS = 4200`
- `MAX_CONTEXT_CHUNKS = 6`
- `MEMORY_MAX_EXCHANGES = 5`

## services/rag_pipeline.py

### Dataclass
`ProcessedDocument`

Fields:
- `file_hash`
- `file_name`
- `pdf_bytes`
- `pages`
- `chunks`
- `vector_store`
- `last_query_plan`

### Helpers
- `_serialize_documents(documents)`: tuple serialization for caching.
- `_deserialize_documents(items)`: rebuilds `Document` objects.
- `_cached_extract_pages(pdf_bytes, file_name)`: cached PDF page extraction.
- `_cached_split_chunks(serialized_pages)`: cached chunk generation.
- `_cached_vector_store(serialized_chunks, _embedding_model)`: cached FAISS builder.

### `RAGPipeline` methods
- `__init__(embedding_model)`: stores the embedding model.
- `process_pdf(pdf_bytes, file_name, file_hash)`: full processing pipeline.
- `create_vectorstore(serialized_chunks)`: cached vector-store wrapper.
- `retrieve(vector_store, question)`: adaptive retrieval entry point.
- `_expand_with_neighbors(vector_store, retrieved_documents)`: adds previous and next chunks.
- `_deduplicate_documents(documents)`: deduplicates by chunk index and text.
- `_merge_neighbor_documents(documents)`: merges adjacent same-page chunks.
- `_compress_page_labels(pages)`: compresses page ranges.
- `_get_recent_conversation()`: extracts recent message memory.
- `_document_to_context_block(document)`: formats `[Page N]` blocks.
- `build_context(documents)`: builds the final prompt context.
- `build_fallback_answer(documents, question)`: LLM-free answer synthesis.
- `is_english_like(text)`: heuristic language sanity check.
- `generate_answer(question, documents)`: prompt creation + Ollama invocation + fallback logic.

## utils/chat_manager.py
- `WELCOME_MESSAGE`: default assistant greeting.
- `initialize_chat_state()`: creates `st.session_state.messages`.
- `add_user_message(content)`: appends a user message.
- `add_assistant_message(content)`: appends an assistant message.
- `clear_chat()`: resets chat to the welcome message.

## utils/embeddings.py

### Dataclass
`EmbeddingStatus`

Fields:
- `cache_available`
- `model_available`
- `offline_mode`
- `cache_path`
- `model_name`
- `message`

### Class
`LocalSentenceTransformerEmbeddings(Embeddings)`

Methods:
- `__init__(model_name)`: loads a local sentence-transformer model.
- `embed_documents(texts)`: returns normalized document embeddings.
- `embed_query(text)`: returns one normalized query embedding.

### Functions
- `_get_hf_home()`: resolves the cache root.
- `_repo_cache_dir(model_name)`: maps a model name to a cache directory.
- `_find_cached_snapshot(model_name)`: finds a cached snapshot with `config.json`.
- `check_embedding_cache()`: returns cache state.
- `check_embedding_model_available()`: resolves the first available local embedding model.
- `_build_embedding_model(model_name)`: wrapper constructor.
- `load_embedding_model()`: timed load with user-facing exceptions.
- `get_embedding_model()`: cached resource wrapper.

## utils/health_check.py
Currently not imported by `app.py`.

- `run_startup_verification(preferred_model="phi3")`
- `render_health_panel(status)`

## utils/llm.py

### Dataclass
`OllamaStatus`

Fields:
- `installed`
- `running`
- `model_available`
- `requested_model`
- `selected_model`
- `available_models`
- `detection_status`
- `llm_ready`
- `llm_test_message`
- `message`

### Functions
- `check_ollama_installed()`
- `_list_models()`
- `check_ollama_running()`
- `_extract_model_names(response)`
- `_normalize_model_name(model_name)`
- `_find_matching_model(model_name, available_models)`
- `_get_available_models()`
- `check_model_exists(model_name)`
- `resolve_model_name(preferred_model=DEFAULT_MODEL)`
- `test_ollama_generation(model_name)`
- `get_ollama_status(preferred_model=DEFAULT_MODEL)`
- `get_llm_status()`
- `_generate_response(model_name, prompt)`
- `stream_response(model_name, prompt, timeout_seconds=30)`

## utils/pdf_loader.py
- `PDFProcessingError`
- `extract_pages_from_pdf(pdf_bytes)`: returns page-level `Document` objects.

## utils/pdf_viewer.py
- `render_pdf_viewer(pdf_bytes)`: renders a base64 PDF iframe or the placeholder.

## utils/prompt_template.py
- `get_prompt_template()`: returns the current grounding prompt template with:
  - `conversation_context`
  - `context`
  - `question`

## utils/retriever.py

### Dataclass
`QueryPlan`

Fields:
- `question_type`
- `rewritten_query`
- `target_k`
- `focus_terms`

### Functions
- `_extract_focus_terms(user_question)`
- `_extract_comparison_terms(user_question)`
- `detect_query_plan(user_question)`
- `_contains_bullet_or_list(text)`
- `_tokenize_for_bm25(text)`
- `_document_priority_score(document, plan)`
- `_rerank_documents(documents, plan)`
- `_rrf_fuse(vector_documents, bm25_documents, plan)`
- `_bm25_retrieve(all_documents, query, target_k, plan)`
- `retrieve_relevant_chunks(vector_store, all_documents, user_question, k=RETRIEVAL_TOP_K)`

## utils/text_splitter.py
- `_normalize_paragraph(paragraph)`
- `_looks_like_table(lines)`
- `_looks_like_list(lines)`
- `_table_to_markdown(lines)`
- `_split_into_paragraphs(page_text)`
- `_is_heading(paragraph)`
- `_tail_overlap(text, max_chars)`
- `split_documents_into_chunks(documents)`

Each output chunk contains:
- `page`
- `source`
- `chunk_id`
- `chunk_index`
- `page_chunk_index`
- `section`

## utils/ui.py
- `apply_app_styling()`
- `render_chat_header()`
- `render_message(role, content)`
- `render_suggestion_buttons(suggestions)`
- `render_document_placeholder()`
- `render_status_banner(message)`
- `render_sidebar(status_text)`

## utils/vector_store.py
- `VectorStoreError`
- `create_vector_store(documents, embedding_model)`
- `get_vector_store_document_count(vector_store)`
- `get_vector_store_documents(vector_store)`

## sitecustomize.py
- `_looks_like_streamlit_process()`

Module-level behavior:
- sets `STREAMLIT_SERVER_FILE_WATCHER_TYPE=none` when the process appears to be Streamlit.

## Tests
- `tests/test_embeddings.py`: empty
- `tests/test_pdf.py`: empty
- `tests/test_retrieval.py`: empty

