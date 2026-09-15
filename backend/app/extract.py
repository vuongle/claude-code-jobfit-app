"""PDF text extraction with pypdf."""

import io

from pypdf import PdfReader


class ExtractionError(Exception):
    """Raised when a PDF cannot be read as text."""


def extract_pdf_text(data: bytes) -> str:
    """Extract text from PDF bytes, joining pages with newlines."""
    try:
        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise ExtractionError(f"Could not read PDF: {exc}") from exc
    if not pages:
        raise ExtractionError("PDF has no pages.")
    return "\n".join(pages)