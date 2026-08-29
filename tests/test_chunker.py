"""
Basic unit tests for the Enterprise Knowledge Copilot RAG pipeline.
Run with: pytest tests/
"""
from app.ingestion.chunker import Chunker
from pathlib import Path


def test_chunker_produces_chunks():
    """Chunker should split a long document into multiple chunks."""
    long_text = "This is a sentence about enterprise policy. " * 100
    chunker = Chunker()
    chunks = chunker.split(long_text, {"source": "test.pdf", "category": "test"})
    assert len(chunks) > 1, "Expected multiple chunks from a long document"


def test_chunker_chunks_have_text():
    """Every chunk produced by the chunker must have non-empty text."""
    text = "The company policy states that all employees must adhere to the code of conduct. " * 20
    chunker = Chunker()
    chunks = chunker.split(text, {"source": "test.pdf", "category": "test"})
    for chunk in chunks:
        assert chunk.text.strip(), "Chunk text must not be empty"


def test_chunker_chunks_have_metadata():
    """Every chunk must carry source and category metadata."""
    text = "Corporate governance policy requires board approval for all material decisions. " * 20
    chunker = Chunker()
    chunks = chunker.split(text, {"source": "test.pdf", "category": "test"})
    for chunk in chunks:
        assert "source" in chunk.metadata, "Chunk metadata must contain 'source'"


def test_chunker_single_sentence():
    """A very short document should produce at least one chunk."""
    chunker = Chunker()
    chunks = chunker.split("Short policy statement.", {"source": "test.pdf", "category": "test"})
    assert len(chunks) >= 1, "Expected at least one chunk from a short document"
