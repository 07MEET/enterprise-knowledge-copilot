from fastapi import APIRouter

from app.ingestion.ingest import IngestionPipeline

router = APIRouter()

pipeline = IngestionPipeline()


@router.post(
    "/documents/ingest",
    tags=["Documents"],
)
def ingest_documents(rebuild: bool = False):
    """
    Run document parser and rebuild vector/keyword search databases.
    """
    if rebuild:
        try:
            pipeline.vector_store.client.delete_collection("enterprise_documents")
            pipeline.vector_store.collection = (
                pipeline.vector_store.client.get_or_create_collection(
                    name="enterprise_documents",
                    metadata={"hnsw:space": "cosine"},
                )
            )
        except Exception as e:
            print(f"Error clearing vector store: {e}")

    documents = pipeline.ingest()

    return {
        "documents_processed": len(documents),
        "documents": documents,
    }