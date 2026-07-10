from pathlib import Path

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions


class DocumentParser:
    """
    Enterprise document parser using Docling.
    """

    def __init__(self):
        # Configure OCR options to force text extraction from embedded image/photo pages
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.ocr_options.force_full_page_ocr = True

        self.converter = DocumentConverter(
            format_options={
                "pdf": PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

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