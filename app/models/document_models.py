from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict


class ParsedDocument(BaseModel):
    """
    Document after parsing and normalization.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    raw_path: Path
    markdown_path: Path

    markdown: str

    metadata: dict[str, Any]


class Chunk(BaseModel):
    """
    One chunk produced from a parsed document.
    """

    chunk_id: str

    text: str

    metadata: dict[str, Any]


class RetrievedChunk(BaseModel):
    """
    Chunk returned by the retrieval pipeline.
    """

    chunk: Chunk

    score: float

    retrieval_method: str
    
class EmbeddedChunk(BaseModel):
    """
    Chunk after embedding generation.
    """

    chunk: Chunk

    embedding: list[float]