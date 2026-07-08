# Tech Stack

## Runtime Technologies

| Technology | Purpose | Used in |
|---|---|---|
| Streamlit | UI, caching, reruns, session state | `app.py`, `services/rag_pipeline.py`, `utils/ui.py`, `utils/llm.py`, `utils/embeddings.py` |
| pypdf | PDF parsing | `utils/pdf_loader.py` |
| LangChain Core | `Document`, `PromptTemplate`, `Embeddings` base class | `utils/pdf_loader.py`, `utils/prompt_template.py`, `utils/embeddings.py`, `services/rag_pipeline.py` |
| LangChain Community | FAISS wrapper | `utils/vector_store.py` |
| FAISS | Dense vector retrieval | `utils/vector_store.py` |
| sentence-transformers | Local embedding execution | `utils/embeddings.py` |
| PyTorch | Backend for sentence-transformers | indirect through `sentence-transformers` |
| Ollama Python client | Local LLM client | `utils/llm.py` |
| Ollama daemon | Local model serving | external runtime |
| rank-bm25 | Optional sparse retrieval | `utils/retriever.py` |

## Current Models

### Embeddings
Preferred:
- `BAAI/bge-small-en-v1.5`

Fallback:
- `sentence-transformers/all-MiniLM-L6-v2`

### Ollama LLM
Preferred:
- `tinyllama`

Configured fallbacks:
- `phi3`
- `gemma:2b`
- `mistral`

## requirements.txt

| Package | Version | Directly used now? | Notes |
|---|---:|---|---|
| `streamlit` | `1.57.0` | Yes | app runtime |
| `langchain` | `1.3.0` | No direct import | installed but not explicitly used |
| `langchain-core` | `1.4.0` | Yes | shared primitives |
| `langchain-community` | `0.4.1` | Yes | FAISS |
| `langchain-ollama` | `1.0.0` | No direct import | not used in current code |
| `langchain-text-splitters` | `1.1.2` | No direct import | older splitter dependency |
| `faiss-cpu` | `1.13.2` | Yes | vector index |
| `rank-bm25` | `0.2.2` | Optional | hybrid retrieval path |
| `sentence-transformers` | `5.5.0` | Yes | local embeddings |
| `huggingface_hub` | `1.14.0` | Indirect | cache/model support |
| `transformers` | `5.8.1` | Indirect | sentence-transformers dependency |
| `torch` | `2.12.0` | Indirect | sentence-transformers backend |
| `pypdf` | `6.11.0` | Yes | PDF extraction |
| `ollama` | `0.6.0` | Yes | LLM client |

## RAG Techniques Actually Implemented

| Technique | Current implementation |
|---|---|
| Chunking | custom paragraph-aware chunker |
| Heading preservation | yes, via `_is_heading()` and `section` metadata |
| List preservation | yes, basic syntax-based handling |
| Table preservation | yes, basic markdown conversion for simple tables |
| Embeddings | normalized local sentence-transformer embeddings |
| Dense retrieval | FAISS MMR |
| Sparse retrieval | optional BM25 |
| Fusion | reciprocal rank fusion |
| Adaptive retrieval | heuristic question classification and query rewrite |
| Context expansion | previous/next chunk inclusion |
| Context cleaning | dedupe + merge adjacent chunks |
| Memory | recent 5 exchanges |
| LLM invocation | local Ollama blocking call |

## Repository Artifacts Not Used By Core Runtime

| Artifact | Status |
|---|---|
| `.env` | present but unused by current code |
| `current_packages.txt` | informational snapshot only |
| `utils/health_check.py` | unused by main app |
| `tests/*.py` | present but empty |
| `uploaded_pdfs/` | directory present, not actively written by current code |
| `vectorstore/` | directory present, not actively written by current code |

