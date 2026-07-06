from pathlib import Path
from typing import List

import fitz
from docx import Document


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def load_documents(documents_path: str) -> List[dict]:
    """
    Load all supported documents from a folder.
    """

    documents = []

    for file in Path(documents_path).rglob("*"):

        if not file.is_file():
            continue

        if file.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        text = ""

        if file.suffix.lower() == ".pdf":
            text = load_pdf(file)

        elif file.suffix.lower() == ".docx":
            text = load_docx(file)

        elif file.suffix.lower() == ".txt":
            text = file.read_text(encoding="utf-8")

        documents.append(
            {
                "filename": file.name,
                "filepath": str(file),
                "extension": file.suffix.lower(),
                "text": text,
            }
        )

    return documents


def load_pdf(path: Path) -> str:

    doc = fitz.open(path)

    text = ""

    for page in doc:
        text += page.get_text()

    return text


def load_docx(path: Path) -> str:

    doc = Document(path)

    return "\n".join(
        paragraph.text
        for paragraph in doc.paragraphs
    )