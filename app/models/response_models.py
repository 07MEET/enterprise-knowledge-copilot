from typing import List

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """
    A supporting citation returned with the answer.
    """
    
    id: int | None = None
    source: str
    page: int | str | None = None
    section: str | None = None
    snippet: str | None = None


class QueryResponse(BaseModel):
    """
    Final response returned to the client.
    """

    answer: str
    citations: List[Citation] = Field(default_factory=list)
    model_used: str | None = None

    confidence: float

    unverified_information: List[str] = Field(default_factory=list)