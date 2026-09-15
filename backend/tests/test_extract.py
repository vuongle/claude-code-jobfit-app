"""Unit tests for PDF text extraction."""

import pytest

from app.extract import ExtractionError, extract_pdf_text


def test_extracts_text_from_fixture_pdf(fixture_pdf_bytes):
    text = extract_pdf_text(fixture_pdf_bytes)
    assert "Marketing" in text
    assert len(text) > 200


@pytest.mark.parametrize("data", [b"%PDF-1.4 this is not a real pdf", b""])
def test_invalid_pdf_raises(data):
    with pytest.raises(ExtractionError):
        extract_pdf_text(data)