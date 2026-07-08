import re

from langchain_core.documents import Document

from config import CHUNK_OVERLAP, CHUNK_SIZE


def _normalize_paragraph(paragraph: str) -> str:
    lines = [line.rstrip() for line in paragraph.splitlines() if line.strip()]
    if not lines:
        return ""

    if _looks_like_table(lines):
        return _table_to_markdown(lines)

    if _looks_like_list(lines):
        cleaned_lines = [re.sub(r"\s+", " ", line).strip() for line in lines]
        return "\n".join(cleaned_lines)

    return re.sub(r"\s+", " ", " ".join(lines)).strip()


def _looks_like_table(lines: list[str]) -> bool:
    if len(lines) < 2:
        return False
    spaced_rows = sum(1 for line in lines[:6] if re.search(r"\S\s{2,}\S", line))
    return spaced_rows >= 2


def _looks_like_list(lines: list[str]) -> bool:
    return any(re.match(r"^(\d+[\).\s]|[-*•])", line.strip()) for line in lines)


def _table_to_markdown(lines: list[str]) -> str:
    rows: list[list[str]] = []
    for line in lines:
        columns = [part.strip() for part in re.split(r"\s{2,}", line.strip()) if part.strip()]
        if len(columns) >= 2:
            rows.append(columns)

    if len(rows) < 2:
        return "\n".join(lines)

    column_count = max(len(row) for row in rows)
    padded_rows = [row + [""] * (column_count - len(row)) for row in rows]
    header = "| " + " | ".join(padded_rows[0]) + " |"
    divider = "| " + " | ".join(["---"] * column_count) + " |"
    body = ["| " + " | ".join(row) + " |" for row in padded_rows[1:]]
    return "\n".join([header, divider, *body])


def _split_into_paragraphs(page_text: str) -> list[str]:
    raw_parts = re.split(r"\n\s*\n+", page_text)
    paragraphs: list[str] = []
    for raw_part in raw_parts:
        normalized = _normalize_paragraph(raw_part)
        if normalized:
            paragraphs.append(normalized)
    return paragraphs


def _is_heading(paragraph: str) -> bool:
    plain = paragraph.replace("\n", " ").strip()
    if not plain or len(plain) > 120:
        return False
    words = plain.split()
    if len(words) > 16:
        return False
    return plain.isupper() or plain.endswith(":") or sum(word[:1].isupper() for word in words) >= max(2, len(words) - 1)


def _tail_overlap(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text

    sentences = re.split(r"(?<=[.!?])\s+", text)
    selected: list[str] = []
    total = 0
    for sentence in reversed(sentences):
        total += len(sentence) + 1
        selected.append(sentence)
        if total >= max_chars:
            break
    return " ".join(reversed(selected)).strip()


def split_documents_into_chunks(documents: list[Document]) -> list[Document]:
    chunks: list[Document] = []
    global_chunk_index = 0

    for page_document in documents:
        page_number = int(page_document.metadata.get("page", 0))
        source_name = page_document.metadata.get("source", "uploaded.pdf")
        paragraphs = _split_into_paragraphs(page_document.page_content)

        buffer_parts: list[str] = []
        current_heading = ""
        page_chunk_index = 0

        def flush_chunk() -> None:
            nonlocal buffer_parts, global_chunk_index, page_chunk_index
            chunk_text = "\n\n".join(part for part in buffer_parts if part).strip()
            if len(chunk_text) < max(120, CHUNK_SIZE // 3) and chunks and int(chunks[-1].metadata.get("page", 0)) == page_number:
                merged_text = chunks[-1].page_content.rstrip() + "\n\n" + chunk_text
                chunks[-1] = Document(page_content=merged_text, metadata=chunks[-1].metadata)
            elif chunk_text:
                chunk_id = f"{source_name}:p{page_number}:c{page_chunk_index}"
                chunks.append(
                    Document(
                        page_content=chunk_text,
                        metadata={
                            **page_document.metadata,
                            "page": page_number,
                            "source": source_name,
                            "chunk_id": chunk_id,
                            "chunk_index": global_chunk_index,
                            "page_chunk_index": page_chunk_index,
                            "section": current_heading or page_document.metadata.get("section", ""),
                        },
                    )
                )
                global_chunk_index += 1
                page_chunk_index += 1
            buffer_parts = []

        for paragraph in paragraphs:
            if _is_heading(paragraph):
                if buffer_parts:
                    flush_chunk()
                current_heading = paragraph
                buffer_parts = [paragraph]
                continue

            candidate_parts = [*buffer_parts, paragraph] if buffer_parts else ([current_heading, paragraph] if current_heading else [paragraph])
            candidate_text = "\n\n".join(part for part in candidate_parts if part).strip()

            if buffer_parts and len(candidate_text) > CHUNK_SIZE:
                previous_text = "\n\n".join(buffer_parts).strip()
                overlap_text = _tail_overlap(previous_text, CHUNK_OVERLAP)
                flush_chunk()
                buffer_parts = [part for part in [current_heading, overlap_text, paragraph] if part]
            else:
                buffer_parts = candidate_parts

        if buffer_parts:
            flush_chunk()

    return chunks
