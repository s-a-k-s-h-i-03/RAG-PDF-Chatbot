# Improvements

## Performance Analysis

## Likely Bottlenecks

### Embedding Model Load
Current behavior:
- loads `SentenceTransformer` locally
- cached with `@st.cache_resource`

Impact:
- startup delay on first embedding use

### PDF Extraction
Current behavior:
- text-only extraction through `pypdf`

Impact:
- scanned PDFs and complex layouts remain weak cases

### Vector Store Build
Current behavior:
- FAISS is rebuilt once per processed document in the active app process

Impact:
- acceptable for small and medium PDFs
- no persistence across full app restarts

### Retrieval
Current behavior:
- FAISS MMR runs every query
- BM25 corpus is rebuilt every query if the package is installed

Impact:
- BM25 is the biggest avoidable per-query overhead

### Generation
Current behavior:
- Ollama call is blocking
- pseudo-streaming starts only after full completion

Impact:
- slower perceived response start

## Improvement Opportunities

| Stage | Improvement | Expected impact | Difficulty | Trade-off |
|---|---|---:|---:|---|
| Retrieval | Cache BM25 index per processed document | High | Medium | More memory per active document |
| Retrieval | Add one-retry self-check when answer is incomplete | High | Medium | Higher worst-case latency |
| Context | Use plan-specific context limits | Medium | Low | Slightly more branching |
| Prompting | Remove duplicate citation insertion points | Medium | Low | None |
| Generation | Use true Ollama streaming | Medium | Medium | More complex handling |
| Parsing | Add OCR for scanned PDFs | High | High | More CPU and dependencies |
| Persistence | Save FAISS by PDF hash | Medium | Medium | Disk management |
| Testing | Add real tests | High for maintainability | Medium | Fixture work required |

## Stage Details

### BM25 Cache
Current issue:
- `_bm25_retrieve()` rebuilds tokenized corpus on every query

Recommended change:
- create BM25 artifacts during `process_pdf()`
- attach them to `ProcessedDocument`

### Self-Check Retry
Current issue:
- there is no second retrieval/generation attempt if the first answer is clearly incomplete

Recommended change:
- inspect answer length and focus-term coverage
- re-retrieve once with expanded scope

### Citation Unification
Current issue:
- both pipeline and app can add `Source:`

Recommended change:
- centralize citation formatting in one layer

### True Streaming
Current issue:
- `stream_response()` yields whitespace-split chunks after full completion

Recommended change:
- use actual streaming support from Ollama

## Maintainability Risks

- empty tests
- stale README risk
- optional dependency path for BM25
- watcher workaround hidden in startup hook

