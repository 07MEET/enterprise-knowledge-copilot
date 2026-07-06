from app.models.response_models import Citation, QueryResponse


def answer_question(question: str) -> QueryResponse:
    """
    Temporary implementation.

    This function will later execute the complete RAG pipeline.
    """

    return QueryResponse(
        answer=f"You asked: {question}",

        citations=[
            Citation(
                source="Demo Document",
                page=1,
                section="Introduction",
            )
        ],

        confidence=1.0,

        unverified_information=[],
    )