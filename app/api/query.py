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

            
    return answer_question(request.question, request.llm_provider, request.fast_mode)

from fastapi.responses import StreamingResponse

@router.post(
    "/query/stream",
    tags=["Query"],
)
def query_stream(request: QueryRequest):
    from app.services.query_service import stream_answer_question


    return StreamingResponse(
        stream_answer_question(request.question, request.history, request.llm_provider),
        media_type="text/event-stream"
    )


@router.post(
    "/debug_retrieve",
    tags=["Query"],
)
def debug_retrieve(request: QueryRequest):
    from app.retrieval.hybrid_retriever import HybridRetriever
    retriever = HybridRetriever()
    chunks = retriever.retrieve(request.question)
    return [
        {
            "score": c.score,
            "method": c.retrieval_method,
            "text": c.chunk.text,
            "source": c.chunk.metadata.get("source"),
            "page": c.chunk.metadata.get("page"),
            "section": c.chunk.metadata.get("h1") or c.chunk.metadata.get("h2") or c.chunk.metadata.get("section")
        }
        for c in chunks
    ]