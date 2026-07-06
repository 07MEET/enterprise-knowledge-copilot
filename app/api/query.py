from fastapi import APIRouter

from app.models.request_models import QueryRequest
from app.models.response_models import QueryResponse
from app.services.query_service import answer_question

router = APIRouter()


@router.post(
    "/query",
    response_model=QueryResponse,
    tags=["Query"],
)
def query(request: QueryRequest):
    return answer_question(request.question)