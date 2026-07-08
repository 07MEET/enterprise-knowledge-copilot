from fastapi import APIRouter

from app.ingestion.ingest import IngestionPipeline

router = APIRouter()

pipeline = IngestionPipeline()


@router.post(
    "/documents/ingest",
    tags=["Documents"],
)
def ingest_documents():

    documents = pipeline.ingest()

    return {
        "documents_processed": len(documents),
        "documents": documents,
    }