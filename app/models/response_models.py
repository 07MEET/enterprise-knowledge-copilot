from typing import List

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """
    A supporting citation returned with the answer.
    """

    source: str
    page: int | None = None
    section: str | None = None


class QueryResponse(BaseModel):
    """
    Final response returned to the client.
    """

    answer: str

    citations: List[Citation] = Field(default_factory=list)

    confidence: float

    unverified_information: List[str] = Field(default_factory=list)