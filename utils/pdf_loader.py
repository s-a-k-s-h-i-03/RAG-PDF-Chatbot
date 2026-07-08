from io import BytesIO

from langchain_core.documents import Document
from pypdf import PdfReader


class PDFProcessingError(RuntimeError):
    """Raised when the uploaded PDF cannot be processed."""


def extract_pages_from_pdf(pdf_bytes: bytes) -> list[Document]:
    if not pdf_bytes:
        raise PDFProcessingError("Please upload a PDF file before processing.")

    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except Exception as exc:
        raise PDFProcessingError(
            "The uploaded PDF could not be read. Please upload a valid, non-corrupted PDF file."
        ) from exc

    pages: list[Document] = []
    for page_index, page in enumerate(reader.pages, start=1):
        try:
            page_text = (page.extract_text() or "").strip()
        except Exception:
            page_text = ""

        if page_text:
            pages.append(
                Document(
                    page_content=page_text,
                    metadata={"page": page_index},
                )
            )

    if not pages:
        raise PDFProcessingError(
            "No readable text was found in this PDF. Try another PDF with selectable text."
        )

    return pages
