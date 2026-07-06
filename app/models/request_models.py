from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """
    Incoming query from the user.
    """

    question: str = Field(
        ...,
        min_length=3,
        description="User question to answer from the knowledge base."
    )