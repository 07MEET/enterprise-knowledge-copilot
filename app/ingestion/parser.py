from pathlib import Path

from docling.document_converter import DocumentConverter


class DocumentParser:
    """
    Enterprise document parser using Docling.
    """

    def __init__(self):
        self.converter = DocumentConverter()

    def parse(self, file_path: Path):
        """
        Parse a single document.

        Returns
        -------
        DoclingDocument
        """

        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        result = self.converter.convert(file_path)

        return result.document