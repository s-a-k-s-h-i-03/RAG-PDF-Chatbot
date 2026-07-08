from dataclasses import dataclass
import re

import streamlit as st
from langchain_core.documents import Document

from config import (
    DEFAULT_MODEL,
    LLM_TIMEOUT_SECONDS,
    MAX_CONTEXT_CHARS,
    MAX_CONTEXT_CHUNKS,
    MEMORY_MAX_EXCHANGES,
    RETRIEVAL_TOP_K,
)
from utils.llm import OllamaSetupError, get_llm_status, stream_response
from utils.pdf_loader import PDFProcessingError, extract_pages_from_pdf
from utils.prompt_template import get_prompt_template
from utils.retriever import QueryPlan, RetrievalError, retrieve_relevant_chunks
from utils.text_splitter import split_documents_into_chunks
from utils.vector_store import (
    VectorStoreError,
    create_vector_store,
    get_vector_store_documents,
)


@dataclass
class ProcessedDocument:
    file_hash: str
    file_name: str
    pdf_bytes: bytes
    pages: list[Document]
    chunks: list[Document]
    vector_store: object
    last_query_plan: QueryPlan | None = None


def _serialize_documents(documents: list[Document]) -> tuple[tuple[str, tuple[tuple[str, object], ...]], ...]:
    return tuple(
        (
            document.page_content,
            tuple(sorted(document.metadata.items())),
        )
        for document in documents
    )


def _deserialize_documents(items: tuple[tuple[str, tuple[tuple[str, object], ...]], ...]) -> list[Document]:
    return [
        Document(page_content=page_content, metadata=dict(metadata_items))
        for page_content, metadata_items in items
    ]


@st.cache_data(show_spinner=False)
def _cached_extract_pages(pdf_bytes: bytes, file_name: str) -> tuple[tuple[str, tuple[tuple[str, object], ...]], ...]:
    pages = extract_pages_from_pdf(pdf_bytes)
    for page in pages:
        page.metadata["source"] = file_name
    return _serialize_documents(pages)


@st.cache_data(show_spinner=False)
def _cached_split_chunks(serialized_pages: tuple[tuple[str, tuple[tuple[str, object], ...]], ...]) -> tuple[tuple[str, tuple[tuple[str, object], ...]], ...]:
    pages = _deserialize_documents(serialized_pages)
    chunks = split_documents_into_chunks(pages)
    return _serialize_documents(chunks)


@st.cache_resource(show_spinner=False)
def _cached_vector_store(
    serialized_chunks: tuple[tuple[str, tuple[tuple[str, object], ...]], ...],
    _embedding_model,
):
    chunks = _deserialize_documents(serialized_chunks)
    return create_vector_store(chunks, _embedding_model)


class RAGPipeline:
    """Reusable local RAG pipeline for PDF chat."""

    def __init__(self, embedding_model):
        self.embedding_model = embedding_model

    def process_pdf(self, pdf_bytes: bytes, file_name: str, file_hash: str) -> ProcessedDocument:
        serialized_pages = _cached_extract_pages(pdf_bytes, file_name)
        pages = _deserialize_documents(serialized_pages)
        serialized_chunks = _cached_split_chunks(serialized_pages)
        chunks = _deserialize_documents(serialized_chunks)
        if not chunks:
            raise PDFProcessingError("No text chunks could be created from the uploaded PDF.")

        vector_store = self.create_vectorstore(serialized_chunks)
        return ProcessedDocument(
            file_hash=file_hash,
            file_name=file_name,
            pdf_bytes=pdf_bytes,
            pages=pages,
            chunks=chunks,
            vector_store=vector_store,
        )

    def create_vectorstore(self, serialized_chunks):
        return _cached_vector_store(serialized_chunks, self.embedding_model)

    def retrieve(self, vector_store, question: str) -> list[Document]:
        all_documents = get_vector_store_documents(vector_store)
        retrieved, query_plan = retrieve_relevant_chunks(
            vector_store,
            all_documents,
            question,
            k=RETRIEVAL_TOP_K,
        )
        self.last_query_plan = query_plan
        return self._expand_with_neighbors(vector_store, retrieved)

    def _expand_with_neighbors(self, vector_store, retrieved_documents: list[Document]) -> list[Document]:
        all_documents = get_vector_store_documents(vector_store)
        if not all_documents:
            return retrieved_documents

        by_index = {
            int(document.metadata.get("chunk_index", -1)): document
            for document in all_documents
            if document.metadata.get("chunk_index") is not None
        }

        selected_indexes: set[int] = set()
        for document in retrieved_documents:
            chunk_index = int(document.metadata.get("chunk_index", -1))
            for neighbor_index in (chunk_index - 1, chunk_index, chunk_index + 1):
                if neighbor_index in by_index:
                    selected_indexes.add(neighbor_index)

        expanded = [by_index[index] for index in sorted(selected_indexes)]
        return expanded or retrieved_documents

    def _deduplicate_documents(self, documents: list[Document]) -> list[Document]:
        seen: set[tuple[int, str]] = set()
        unique_documents: list[Document] = []
        for document in documents:
            signature = (
                int(document.metadata.get("chunk_index", -1)),
                document.page_content.strip(),
            )
            if signature in seen:
                continue
            seen.add(signature)
            unique_documents.append(document)
        return unique_documents

    def _merge_neighbor_documents(self, documents: list[Document]) -> list[Document]:
        if not documents:
            return []

        sorted_documents = sorted(
            self._deduplicate_documents(documents),
            key=lambda document: (
                int(document.metadata.get("page", 0)),
                int(document.metadata.get("chunk_index", 0)),
            ),
        )

        merged: list[Document] = []
        current = sorted_documents[0]

        for document in sorted_documents[1:]:
            current_page = int(current.metadata.get("page", 0))
            next_page = int(document.metadata.get("page", 0))
            current_index = int(current.metadata.get("chunk_index", -1))
            next_index = int(document.metadata.get("chunk_index", -1))

            if next_page == current_page and next_index == current_index + 1:
                merged_text = current.page_content.rstrip() + "\n\n" + document.page_content.lstrip()
                merged_metadata = dict(current.metadata)
                merged_metadata["merged_until_chunk_index"] = next_index
                current = Document(page_content=merged_text, metadata=merged_metadata)
            else:
                merged.append(current)
                current = document

        merged.append(current)
        return merged[:MAX_CONTEXT_CHUNKS]

    def _compress_page_labels(self, pages: list[int]) -> str:
        if not pages:
            return "Page not available"

        ranges: list[str] = []
        start = pages[0]
        end = pages[0]
        for page in pages[1:]:
            if page == end + 1:
                end = page
            else:
                ranges.append(f"Page {start}" if start == end else f"Pages {start}-{end}")
                start = end = page
        ranges.append(f"Page {start}" if start == end else f"Pages {start}-{end}")
        return ", ".join(ranges)

    def _get_recent_conversation(self) -> str:
        messages = st.session_state.get("messages", [])
        history = [message for message in messages if message.get("role") in {"user", "assistant"}]
        if len(history) <= 1:
            return "No prior conversation."

        recent_messages = history[-(MEMORY_MAX_EXCHANGES * 2):]
        formatted = []
        for message in recent_messages:
            role = "User" if message["role"] == "user" else "Assistant"
            content = re.sub(r"\s+", " ", message["content"]).strip()
            formatted.append(f"{role}: {content[:240]}")
        return "\n".join(formatted)

    def _document_to_context_block(self, document: Document) -> str:
        page_number = int(document.metadata.get("page", 0))
        heading = f"[Page {page_number}]"
        body = document.page_content.strip()
        return f"{heading}\n{body}"

    def build_context(self, documents: list[Document]) -> tuple[str, list[int]]:
        merged_documents = self._merge_neighbor_documents(documents)
        context_blocks: list[str] = []
        pages: list[int] = []
        current_length = 0

        for document in merged_documents:
            block = self._document_to_context_block(document)
            projected_length = current_length + len(block) + 2
            if context_blocks and projected_length > MAX_CONTEXT_CHARS:
                break
            context_blocks.append(block)
            current_length = projected_length
            page_number = int(document.metadata.get("page", 0))
            if page_number:
                pages.append(page_number)

        return "\n\n".join(context_blocks).strip(), sorted(set(pages))

    def build_fallback_answer(self, documents: list[Document], question: str) -> tuple[str, list[int]]:
        merged_documents = self._merge_neighbor_documents(documents)
        if not merged_documents:
            return "I could not find this information in the uploaded PDF.", []

        pages = sorted(
            {
                int(document.metadata.get("page", 0))
                for document in merged_documents
                if int(document.metadata.get("page", 0)) > 0
            }
        )

        snippets: list[str] = []
        keywords = {token.lower() for token in re.findall(r"[A-Za-z]{4,}", question)}
        for document in merged_documents[:MAX_CONTEXT_CHUNKS]:
            lines = [line.strip() for line in document.page_content.splitlines() if line.strip()]
            matched_lines = [line for line in lines if any(keyword in line.lower() for keyword in keywords)]
            selected = matched_lines[:5] if matched_lines else lines[:5]
            if selected:
                snippets.append(" ".join(selected))

        body = "\n".join(f"- {snippet[:320]}" for snippet in snippets[:5]) or "- I could not find this information in the uploaded PDF."
        source_label = self._compress_page_labels(pages)
        answer = (
            "Here is what the uploaded document provides:\n\n"
            f"{body}\n\n"
            f"Source: {source_label}"
        )
        return answer, pages

    def is_english_like(self, text: str) -> bool:
        lowered = text.lower()
        non_english_markers = [
            "pas de",
            "traduction",
            "contenu",
            "réponse",
            "français",
            "dans le document",
        ]
        marker_hits = sum(1 for marker in non_english_markers if marker in lowered)
        return marker_hits < 2

    def generate_answer(self, question: str, documents: list[Document]):
        ollama_status = get_llm_status()
        context, pages = self.build_context(documents)
        if not context:
            raise RetrievalError("I could not find this information in the uploaded PDF.")

        conversation_context = self._get_recent_conversation()
        fallback_answer, fallback_pages = self.build_fallback_answer(documents, question)

        if not ollama_status.model_available or not ollama_status.selected_model:
            return iter([fallback_answer]), fallback_pages
        if not ollama_status.llm_ready:
            return iter([fallback_answer]), fallback_pages

        prompt = get_prompt_template().format(
            conversation_context=conversation_context,
            context=context,
            question=question,
        )
        try:
            generated_answer = "".join(
                list(
                    stream_response(
                        ollama_status.selected_model or DEFAULT_MODEL,
                        prompt,
                        timeout_seconds=LLM_TIMEOUT_SECONDS,
                    )
                )
            ).strip()
            if not generated_answer or not self.is_english_like(generated_answer):
                return iter([fallback_answer]), fallback_pages

            if pages and "source:" not in generated_answer.lower():
                generated_answer = f"{generated_answer}\n\nSource: {self._compress_page_labels(pages)}"

            return iter([generated_answer]), pages
        except OllamaSetupError:
            return iter([fallback_answer]), fallback_pages
