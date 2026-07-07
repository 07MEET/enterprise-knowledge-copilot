from pathlib import Path

from docling.document_converter import DocumentConverter


class DocumentParser:
    """
    Enterprise document parser.

    Uses Docling to convert enterprise documents into structured Markdown.
    """

    def __init__(self):
        self.converter = DocumentConverter()

    def parse(self, file_path: Path):
        """
        Parse a single document.

        Parameters
        ----------
        file_path : Path

        Returns
        -------
        DoclingDocument
        """

        result = self.converter.convert(file_path)

        return result.document