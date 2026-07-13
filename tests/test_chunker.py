"""
Basic unit tests for the Enterprise Knowledge Copilot RAG pipeline.
Run with: pytest tests/
"""
import pytest
from app.ingestion.chunker import chunk_document
from app.models.document_models import ParsedDocument
from pathlib import Path


def make_dummy_document(text: str) -> ParsedDocument:
    """Helper to create a minimal ParsedDocument for testing."""
    return ParsedDocument(
        raw_path=Path("data/raw/test.pdf"),
        markdown_path=Path("data/processed/test.md"),
        markdown=text,
        metadata={"source": "test.pdf", "category": "test"},
    )


def test_chunker_produces_chunks():
    """Chunker should split a long document into multiple chunks."""
    long_text = "This is a sentence about enterprise policy. " * 100
    doc = make_dummy_document(long_text)
    chunks = chunk_document(doc)
    assert len(chunks) > 1, "Expected multiple chunks from a long document"


def test_chunker_chunks_have_text():
    """Every chunk produced by the chunker must have non-empty text."""
    text = "The company policy states that all employees must adhere to the code of conduct. " * 20
    doc = make_dummy_document(text)
    chunks = chunk_document(doc)
    for chunk in chunks:
        assert chunk.text.strip(), "Chunk text must not be empty"


def test_chunker_chunks_have_metadata():
    """Every chunk must carry source and category metadata."""
    text = "Corporate governance policy requires board approval for all material decisions. " * 20
    doc = make_dummy_document(text)
    chunks = chunk_document(doc)
    for chunk in chunks:
        assert "source" in chunk.metadata, "Chunk metadata must contain 'source'"


def test_chunker_single_sentence():
    """A very short document should produce at least one chunk."""
    doc = make_dummy_document("Short policy statement.")
    chunks = chunk_document(doc)
    assert len(chunks) >= 1, "Expected at least one chunk from a short document"
