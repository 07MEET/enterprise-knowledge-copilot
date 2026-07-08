from pathlib import Path

from app.config.settings import settings
from app.ingestion.metadata import generate_metadata
from app.ingestion.parser import DocumentParser
from app.models.document_models import ParsedDocument

class IngestionPipeline:
    """
    Enterprise document ingestion pipeline.
    """

    def __init__(self):

        self.parser = DocumentParser()

        self.raw_dir = settings.RAW_DATA_DIR

        self.processed_dir = settings.PROCESSED_DATA_DIR

    def ingest(self):

        parsed_documents = []

        for file_path in self.raw_dir.rglob("*"):

            if not file_path.is_file():
                continue

            print(f"Processing: {file_path.name}")

            document = self.parser.parse(file_path)

            markdown = document.export_to_markdown()

            metadata = generate_metadata(file_path)

            category_folder = (
                self.processed_dir
                / file_path.parent.name
            )

            category_folder.mkdir(
                parents=True,
                exist_ok=True,
            )

            output_file = (
                category_folder
                / f"{file_path.stem}.md"
            )

            output_file.write_text(
                markdown,
                encoding="utf-8",
            )

            parsed_documents.append(
                ParsedDocument(
                    raw_path=file_path,
                    markdown_path=output_file,
                    markdown=markdown,
                    metadata=metadata,
                )
            )

        return parsed_documents