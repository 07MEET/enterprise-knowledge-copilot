from fastapi import FastAPI

from app.api.root import router as root_router
from app.api.health import router as health_router
from app.api.query import router as query_router
from app.api.documents import router as documents_router

app = FastAPI(
    title="Enterprise Knowledge Copilot",
    description="Enterprise RAG API",
    version="1.0.0",
)

app.include_router(root_router)
app.include_router(health_router)
app.include_router(query_router)
app.include_router(documents_router)