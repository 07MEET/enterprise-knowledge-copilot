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
    llm_provider: str | None = Field(
        default=None,
        description="Optional override for LLM provider (local or openrouter)"
    )
    fast_mode: bool = Field(
        default=False,
        description="If True, bypasses the LLM-based claim verification step to generate responses faster."
    )

    history: list[dict] = Field(
        default_factory=list,
        description="List of previous conversational turns. Each dict must contain 'role' and 'content' keys."
    )