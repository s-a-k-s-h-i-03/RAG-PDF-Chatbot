# Developer Guide

## Setup

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
ollama serve
ollama pull tinyllama
streamlit run app.py
```

## Documentation Map

- [architecture.md](/C:/Users/saksh/RAG-PDF-Chatbot/docs/architecture.md)
- [workflow.md](/C:/Users/saksh/RAG-PDF-Chatbot/docs/workflow.md)
- [modules.md](/C:/Users/saksh/RAG-PDF-Chatbot/docs/modules.md)
- [tech-stack.md](/C:/Users/saksh/RAG-PDF-Chatbot/docs/tech-stack.md)
- [improvements.md](/C:/Users/saksh/RAG-PDF-Chatbot/docs/improvements.md)

## Important Current Behaviors

### Streamlit Watcher Disabled
The project disables Streamlit file watching to avoid the `torch.classes` watcher warning. This affects hot reload.

Controlled by:
- [.streamlit/config.toml](/C:/Users/saksh/RAG-PDF-Chatbot/.streamlit/config.toml)
- [sitecustomize.py](/C:/Users/saksh/RAG-PDF-Chatbot/sitecustomize.py)

### Embedding Model Resolution
Embeddings are resolved from local cache in this order:

1. `BAAI/bge-small-en-v1.5`
2. `sentence-transformers/all-MiniLM-L6-v2`

### Optional BM25
If `rank-bm25` is missing:

- app still runs
- hybrid retrieval becomes FAISS-only

## Maintenance Hotspots

### `app.py`
Watch for:
- session-state drift
- duplicate source rendering
- rerun timing

### `services/rag_pipeline.py`
Watch for:
- cache compatibility
- context truncation
- fallback answer path

### `utils/retriever.py`
Watch for:
- planner heuristics
- BM25 availability
- reranking bias
- per-query BM25 rebuild cost

### `utils/embeddings.py`
Watch for:
- cache assumptions
- model fallback surprises
- startup latency

### `utils/llm.py`
Watch for:
- timeout behavior
- model fallback order
- pseudo-streaming behavior

## Recommended Regression Checks

After changing retrieval or generation:

1. Start the app
2. Process a known PDF
3. Ask:
   - summary question
   - definition question
   - list question
   - comparison question
   - follow-up question
4. Confirm:
   - no crash
   - answer appears
   - source pages appear
   - no obvious duplicate citation block

## Suggested Next Refactors

1. Cache BM25 index
2. Add self-check retry
3. Unify citation formatting
4. Add true Ollama streaming
5. Add automated tests

