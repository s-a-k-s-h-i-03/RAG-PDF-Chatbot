# Local PDF AI Assistant

Local PDF question answering app built with Streamlit, FAISS, `sentence-transformers`, and Ollama.

The current codebase:

- runs fully locally
- processes one uploaded PDF at a time
- uses adaptive retrieval planning
- uses FAISS MMR retrieval
- optionally uses BM25 fusion when `rank-bm25` is installed
- uses Ollama for local answer generation

## Quick Start

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
ollama serve
ollama pull tinyllama
streamlit run app.py
```

## Current Runtime Notes

- preferred LLM model in code: `tinyllama`
- Ollama fallback models: `phi3`, `gemma:2b`, `mistral`
- preferred embedding model in code: `BAAI/bge-small-en-v1.5`
- embedding fallback model: `sentence-transformers/all-MiniLM-L6-v2`
- Streamlit file watching is intentionally disabled for compatibility with the current PyTorch stack

## Documentation

Detailed technical documentation is available in [docs/index.md](/C:/Users/saksh/RAG-PDF-Chatbot/docs/index.md).

Main documents:

- [Architecture](/C:/Users/saksh/RAG-PDF-Chatbot/docs/architecture.md)
- [Workflow](/C:/Users/saksh/RAG-PDF-Chatbot/docs/workflow.md)
- [Modules Reference](/C:/Users/saksh/RAG-PDF-Chatbot/docs/modules.md)
- [Tech Stack](/C:/Users/saksh/RAG-PDF-Chatbot/docs/tech-stack.md)
- [Improvements](/C:/Users/saksh/RAG-PDF-Chatbot/docs/improvements.md)
- [Developer Guide](/C:/Users/saksh/RAG-PDF-Chatbot/docs/developer-guide.md)

## Current Features

- sidebar PDF upload and processing flow
- PDF viewer and chat panel in a split layout
- section-aware paragraph chunking
- local sentence-transformer embeddings
- FAISS vector retrieval with MMR
- query-type detection before retrieval
- optional BM25 + FAISS reciprocal-rank fusion
- neighbor chunk expansion
- conversation memory from recent exchanges
- local Ollama inference with source citations

## Known Current Limitations

- automated tests are currently empty placeholders
- Streamlit hot reload is intentionally disabled
- BM25 hybrid retrieval only activates if `rank-bm25` is installed
- source lines can be duplicated in some answer paths

## Repository Layout

```text
RAG-PDF-Chatbot/
|-- app.py
|-- config.py
|-- requirements.txt
|-- README.md
|-- sitecustomize.py
|-- services/
|-- utils/
|-- tests/
`-- docs/
```
