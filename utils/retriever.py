from dataclasses import dataclass
import re

from langchain_core.documents import Document
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ModuleNotFoundError:
    BM25Okapi = None
    BM25_AVAILABLE = False

from config import RETRIEVAL_FETCH_K, RETRIEVAL_LAMBDA_MULT, RETRIEVAL_TOP_K


class RetrievalError(RuntimeError):
    """Raised when semantic retrieval fails."""


@dataclass
class QueryPlan:
    question_type: str
    rewritten_query: str
    target_k: int
    focus_terms: list[str]


def _extract_focus_terms(user_question: str) -> list[str]:
    return [
        token.lower()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", user_question)
        if token.lower() not in {"what", "which", "about", "from", "into", "with", "that", "this", "there", "their"}
    ]


def _extract_comparison_terms(user_question: str) -> list[str]:
    lowered = user_question.lower()
    match = re.search(r"difference between\s+(.+?)\s+and\s+(.+)", lowered)
    if match:
        return [match.group(1).strip(), match.group(2).strip()]

    if " vs " in lowered:
        left, right = lowered.split(" vs ", 1)
        return [left.split()[-1].strip(), right.split()[0].strip()]

    tokens = _extract_focus_terms(user_question)
    return tokens[:2]


def detect_query_plan(user_question: str) -> QueryPlan:
    lowered = user_question.lower().strip()
    focus_terms = _extract_focus_terms(user_question)

    summary_markers = [
        "summary",
        "summarize",
        "overview",
        "what is this document about",
        "main idea",
        "brief of",
    ]
    list_markers = [
        "types of",
        "list",
        "what are the",
        "applications of",
        "steps",
        "features of",
        "examples of",
    ]
    comparison_markers = [
        "difference between",
        "compare",
        "comparison",
        "vs",
        "versus",
    ]
    definition_markers = [
        "what is",
        "define",
        "meaning of",
        "explain",
    ]

    if any(marker in lowered for marker in summary_markers):
        return QueryPlan(
            question_type="summary",
            rewritten_query="Generate a complete summary of the uploaded PDF.",
            target_k=10,
            focus_terms=focus_terms,
        )

    if any(marker in lowered for marker in comparison_markers):
        comparison_terms = _extract_comparison_terms(user_question)
        rewritten = "Compare the following topics from the uploaded PDF: " + " and ".join(comparison_terms)
        return QueryPlan(
            question_type="comparison",
            rewritten_query=rewritten,
            target_k=6,
            focus_terms=comparison_terms,
        )

    if any(marker in lowered for marker in list_markers):
        rewritten = f"Find headings, bullet lists, and enumerated points relevant to: {user_question}"
        return QueryPlan(
            question_type="list",
            rewritten_query=rewritten,
            target_k=6,
            focus_terms=focus_terms,
        )

    if any(marker in lowered for marker in definition_markers):
        rewritten = f"Find the definition and explanation in the uploaded PDF for: {user_question}"
        return QueryPlan(
            question_type="definition",
            rewritten_query=rewritten,
            target_k=4,
            focus_terms=focus_terms,
        )

    return QueryPlan(
        question_type="general",
        rewritten_query=user_question,
        target_k=min(max(RETRIEVAL_TOP_K, 5), 8),
        focus_terms=focus_terms,
    )


def _contains_bullet_or_list(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return any(re.match(r"^(\d+[\).\s]|[-*•])", line) for line in lines)


def _tokenize_for_bm25(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9\-]+", text.lower())


def _document_priority_score(document: Document, plan: QueryPlan) -> float:
    text = document.page_content.lower()
    section = str(document.metadata.get("section", "")).lower()
    score = 0.0

    for term in plan.focus_terms:
        if term and term in text:
            score += 2.0
        if term and term in section:
            score += 2.5

    if plan.question_type == "list":
        if _contains_bullet_or_list(document.page_content):
            score += 3.0
        if section:
            score += 1.0
    elif plan.question_type == "comparison":
        hits = sum(1 for term in plan.focus_terms[:2] if term and term in text)
        if hits >= 2:
            score += 5.0
    elif plan.question_type == "definition":
        first_lines = " ".join(document.page_content.splitlines()[:3]).lower()
        if any(term in first_lines for term in plan.focus_terms):
            score += 2.5
    elif plan.question_type == "summary":
        page_number = int(document.metadata.get("page", 0))
        score += max(0.0, 1.5 - (page_number * 0.05))

    return score


def _rerank_documents(documents: list[Document], plan: QueryPlan) -> list[Document]:
    scored = [
        (
            _document_priority_score(document, plan),
            int(document.metadata.get("page", 0)),
            int(document.metadata.get("chunk_index", 0)),
            document,
        )
        for document in documents
    ]
    scored.sort(key=lambda item: (-item[0], item[1], item[2]))
    return [item[3] for item in scored]


def _rrf_fuse(vector_documents: list[Document], bm25_documents: list[Document], plan: QueryPlan) -> list[Document]:
    fused_scores: dict[tuple[int, str], float] = {}
    document_lookup: dict[tuple[int, str], Document] = {}
    rrf_k = 60

    for rank, document in enumerate(vector_documents, start=1):
        key = (
            int(document.metadata.get("chunk_index", -1)),
            str(document.metadata.get("chunk_id", document.page_content[:60])),
        )
        fused_scores[key] = fused_scores.get(key, 0.0) + (1.0 / (rrf_k + rank))
        document_lookup[key] = document

    for rank, document in enumerate(bm25_documents, start=1):
        key = (
            int(document.metadata.get("chunk_index", -1)),
            str(document.metadata.get("chunk_id", document.page_content[:60])),
        )
        fused_scores[key] = fused_scores.get(key, 0.0) + (1.0 / (rrf_k + rank))
        document_lookup[key] = document

    ranked = sorted(
        (
            (
                score + _document_priority_score(document_lookup[key], plan),
                int(document_lookup[key].metadata.get("page", 0)),
                int(document_lookup[key].metadata.get("chunk_index", 0)),
                document_lookup[key],
            )
            for key, score in fused_scores.items()
        ),
        key=lambda item: (-item[0], item[1], item[2]),
    )
    return [item[3] for item in ranked]


def _bm25_retrieve(all_documents: list[Document], query: str, target_k: int, plan: QueryPlan) -> list[Document]:
    if not BM25_AVAILABLE or not all_documents:
        return []

    tokenized_corpus = [_tokenize_for_bm25(document.page_content) for document in all_documents]
    query_tokens = _tokenize_for_bm25(query)
    if not query_tokens:
        return []

    bm25 = BM25Okapi(tokenized_corpus)
    scores = bm25.get_scores(query_tokens)
    scored_documents = [
        (
            float(score) + _document_priority_score(document, plan),
            int(document.metadata.get("page", 0)),
            int(document.metadata.get("chunk_index", 0)),
            document,
        )
        for score, document in zip(scores, all_documents, strict=False)
    ]
    scored_documents.sort(key=lambda item: (-item[0], item[1], item[2]))
    return [item[3] for item in scored_documents[: max(target_k * 2, 8)]]


def retrieve_relevant_chunks(
    vector_store,
    all_documents: list[Document],
    user_question: str,
    k: int = RETRIEVAL_TOP_K,
) -> tuple[list[Document], QueryPlan]:
    if not user_question or not user_question.strip():
        raise RetrievalError("Please enter a question before asking the assistant.")

    plan = detect_query_plan(user_question)
    target_k = max(3, plan.target_k if plan.target_k else k)
    fetch_k = max(RETRIEVAL_FETCH_K, target_k * 2)

    try:
        retriever = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": target_k,
                "fetch_k": fetch_k,
                "lambda_mult": RETRIEVAL_LAMBDA_MULT,
            },
        )
        documents = retriever.invoke(plan.rewritten_query)
    except Exception as exc:
        raise RetrievalError(
            "Semantic retrieval failed. Please reprocess the document and try again."
        ) from exc

    bm25_documents = _bm25_retrieve(all_documents, plan.rewritten_query, target_k, plan)
    fused_documents = _rrf_fuse(documents, bm25_documents, plan)

    if not fused_documents:
        raise RetrievalError(
            "I could not find this information in the uploaded PDF."
        )

    reranked = _rerank_documents(fused_documents, plan)
    return reranked[:target_k], plan
