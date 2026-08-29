import json
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks

from app.config.settings import settings
from app.ingestion.ingest import IngestionPipeline
from app.storage.vector_store import VectorStore

router = APIRouter()
pipeline = IngestionPipeline()


# Global status state to monitor background indexing process
ingestion_status = {
    "status": "idle",
    "processed": 0,
    "error": None
}


def run_ingest_background(rebuild: bool = False):
    global ingestion_status
    try:
        ingestion_status["status"] = "processing"
        ingestion_status["error"] = None
        
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

        documents = pipeline.ingest(rebuild=rebuild)
        ingestion_status["status"] = "idle"
        ingestion_status["processed"] = len(documents)
        

    except Exception as e:
        ingestion_status["status"] = "failed"
        ingestion_status["error"] = str(e)
        print(f"Background ingestion failed: {e}")


@router.post(
    "/documents/ingest",
    tags=["Documents"],
)
def ingest_documents(background_tasks: BackgroundTasks, rebuild: bool = False):
    """
    Run document parser and rebuild vector/keyword search databases asynchronously.
    """
    global ingestion_status
    if ingestion_status["status"] == "processing":
        return {"message": "Ingestion already in progress.", "status": "processing"}

    background_tasks.add_task(run_ingest_background, rebuild)
    return {"message": "Ingestion started in the background.", "status": "processing"}


@router.get(
    "/documents/ingest/status",
    tags=["Documents"],
)
def get_ingest_status():
    """
    Get the status of the background ingestion process.
    """
    global ingestion_status
    return ingestion_status

def get_web_uploaded_ids() -> set[str]:
    """
    Read the registry of files uploaded via the web interface.
    """
    registry_path = Path("data/web_uploaded.json")
    if not registry_path.exists():
        return set()
    try:
        with open(registry_path, "r") as f:
            data = json.load(f)
            return set(data.get("uploaded_ids", []))
    except Exception:
        return set()


def register_web_uploaded_id(doc_id: str):
    """
    Register a document ID as uploaded from the web.
    """
    registry_path = Path("data/web_uploaded.json")
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    uploaded_ids = get_web_uploaded_ids()
    uploaded_ids.add(doc_id)
    try:
        with open(registry_path, "w") as f:
            json.dump({"uploaded_ids": list(uploaded_ids)}, f)
    except Exception as e:
        print(f"Error registering web upload: {e}")


def unregister_web_uploaded_id(doc_id: str):
    """
    Remove a document ID from the web upload registry on deletion.
    """
    registry_path = Path("data/web_uploaded.json")
    uploaded_ids = get_web_uploaded_ids()
    if doc_id in uploaded_ids:
        uploaded_ids.remove(doc_id)
        try:
            with open(registry_path, "w") as f:
                json.dump({"uploaded_ids": list(uploaded_ids)}, f)
        except Exception as e:
            print(f"Error unregistering web upload: {e}")




@router.post(
    "/documents/upload",
    tags=["Documents"],
)
def upload_document(file: UploadFile = File(...), category: str = Form(...)):
    """
    Upload a document from the web interface.
    Saves it to raw storage and registers it as deletable.
    """
    raw_dir = Path(settings.RAW_DATA_DIR) / category
    raw_dir.mkdir(parents=True, exist_ok=True)

    target_path = raw_dir / file.filename
    try:
        content = file.file.read()
        with open(target_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save uploaded file: {e}"
        )

    doc_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, target_path.as_posix()))
    register_web_uploaded_id(doc_id)

    return {
        "status": "success",
        "document_id": doc_id,
        "filename": file.filename,
        "category": category,
    }


@router.get(
    "/documents",
    tags=["Documents"],
)
def list_documents():
    """
    Scan raw data storage and resolve indexing metadata/chunk status.
    """
    raw_dir = Path(settings.RAW_DATA_DIR)
    if not raw_dir.exists():
        return []

    files = []
    for file_path in raw_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in [
            ".pdf",
            ".docx",
            ".md",
            ".txt",
        ]:
            files.append(file_path)

    vector_store = VectorStore()
    docs_info = []
    web_uploaded_ids = get_web_uploaded_ids()

    for f in files:
        rel_path = f.relative_to(raw_dir)
        category = f.parent.name.replace("_", " ")
        doc_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f.as_posix()))

        # Check chunk count indexed under this document_id
        try:
            res = vector_store.collection.get(
                where={"document_id": doc_id}, include=[]
            )
            chunk_count = len(res["ids"]) if res and "ids" in res else 0
        except Exception:
            chunk_count = 0

        docs_info.append(
            {
                "document_id": doc_id,
                "filename": f.name,
                "category": category,
                "rel_path": rel_path.as_posix(),
                "indexed": chunk_count > 0,
                "chunks": chunk_count,
                "file_size": f.stat().st_size,
                "deletable": doc_id in web_uploaded_ids,
            }
        )

    return docs_info


@router.delete(
    "/documents/{document_id}",
    tags=["Documents"],
)
def delete_document(document_id: str):
    """
    Deletes all chunks of a document from ChromaDB, BM25, and purges source files.
    """
    web_uploaded_ids = get_web_uploaded_ids()
    if document_id not in web_uploaded_ids:
        raise HTTPException(
            status_code=403,
            detail="Deletion of locally copied or core system documents is prohibited.",
        )

    raw_dir = Path(settings.RAW_DATA_DIR)
    target_file = None

    for file_path in raw_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in [
            ".pdf",
            ".docx",
            ".md",
            ".txt",
        ]:
            doc_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, file_path.as_posix()))
            if doc_id == document_id:
                target_file = file_path
                break

    if not target_file:
        raise HTTPException(
            status_code=404, detail="Document file not found in storage."
        )

    # 1. Purge database records in ChromaDB
    try:
        pipeline.vector_store.delete_document(document_id)
    except Exception as e:
        print(f"Error deleting chunks for {document_id}: {e}")

    # 2. Rebuild sparse index to sync BM25 in-memory model
    try:
        from app.retrieval.bm25_retriever import BM25Retriever

        bm25_retriever = BM25Retriever()
        bm25_retriever.rebuild_index()
    except Exception as e:
        print(f"Error rebuilding BM25 index: {e}")

    # 3. Purge physical files from storage
    deleted_raw = False
    deleted_processed = False
    try:
        if target_file.exists():
            target_file.unlink()
            deleted_raw = True
    except Exception as e:
        print(f"Error deleting raw document file {target_file}: {e}")

    # Processed markdown deletion
    try:
        processed_dir = Path(settings.PROCESSED_DATA_DIR)
        rel_path = target_file.relative_to(raw_dir)
        processed_file = (
            processed_dir / rel_path.parent / f"{target_file.stem}.md"
        )
        if processed_file.exists():
            processed_file.unlink()
            deleted_processed = True
    except Exception as e:
        print(f"Error deleting processed file: {e}")

    # Remove from registry
    unregister_web_uploaded_id(document_id)



    return {
        "status": "success",
        "document_id": document_id,
        "filename": target_file.name,
        "deleted_raw": deleted_raw,
        "deleted_processed": deleted_processed,
    }