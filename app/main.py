# Initialize PyTorch CUDA first to prevent library conflicts causing segmentation faults
import torch
from sentence_transformers import SentenceTransformer
device = "cuda" if torch.cuda.is_available() else "cpu"
_ = SentenceTransformer("BAAI/bge-large-en-v1.5", device=device)

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