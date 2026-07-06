from fastapi import APIRouter

from app.models.request_models import QueryRequest
from app.models.response_models import QueryResponse

router = APIRouter()


@router.post("/query", response_model=QueryResponse, tags=["Query"])
def query(request: QueryRequest):
    return QueryResponse(
        answer=f"You asked: {request.question}",
        confidence=1.0,
    )