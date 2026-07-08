from pathlib import Path
from datetime import datetime
import uuid


def generate_metadata(file_path: Path) -> dict:
    """
    Generate metadata for a document.
    """

    category = file_path.parent.name.replace("_", " ")

    return {
        "document_id": str(uuid.uuid4()),
        "source": file_path.name,
        "category": category,
        "document_type": file_path.suffix.lower(),
        "last_updated": datetime.fromtimestamp(
            file_path.stat().st_mtime
        ).isoformat(),
        "access_level": "internal",
    }