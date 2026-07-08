from pathlib import Path
from datetime import datetime
import uuid


def generate_metadata(file_path: Path) -> dict:
    """
    Generate metadata for a document.
    """

    category = file_path.parent.name.replace("_", " ")
    
    # Deterministic document_id based on relative path to avoid duplication on re-indexing
    document_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, file_path.as_posix()))

    return {
        "document_id": document_id,
        "source": file_path.name,
        "category": category,
        "document_type": file_path.suffix.lower(),
        "last_updated": datetime.fromtimestamp(
            file_path.stat().st_mtime
        ).isoformat(),
        "access_level": "internal",
    }