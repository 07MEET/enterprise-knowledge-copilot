import argparse
from pathlib import Path
import sys

from app.config.settings import settings
from app.embeddings.factory import get_embedding_model
from app.ingestion.chunker import Chunker
from app.ingestion.metadata import generate_metadata
from app.ingestion.parser import DocumentParser
from app.models.document_models import ParsedDocument
from app.storage.vector_store import VectorStore


class IngestionPipeline:
    """
    Enterprise document ingestion pipeline.
    """

    def __init__(self):
        """
        Initialize parsing, chunking, storage, and embedding models.
        """
        self.parser = DocumentParser()
        self.chunker = Chunker()
        self.vector_store = VectorStore()
        self.embedder = get_embedding_model()
        self.raw_dir = settings.RAW_DATA_DIR
        self.processed_dir = settings.PROCESSED_DATA_DIR

    def ingest(self, rebuild: bool = False) -> list[ParsedDocument]:
        """
        Run the ingestion pipeline on all raw documents.
        """
        parsed_documents = []

        if not self.raw_dir.exists():
            print(f"Raw data directory does not exist: {self.raw_dir}")
            return []

        # Find files matching supported extensions
        files_to_process = []
        for file_path in self.raw_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in [
                ".pdf",
                ".docx",
                ".md",
                ".txt",
            ]:
                files_to_process.append(file_path)

        if not files_to_process:
            print("No supported documents found to ingest.")
            return []

        print(f"Found {len(files_to_process)} documents to process.")

        for file_path in files_to_process:
            print(f"Processing: {file_path.name}")
            try:
                # 1. Parse document using Docling
                document = self.parser.parse(file_path)
                markdown = document.export_to_markdown()

                # 2. Generate metadata
                metadata = generate_metadata(file_path)
                document_id = metadata["document_id"]

                # 3. Save processed markdown file while preserving category folders
                category_folder = (
                    self.processed_dir
                    / file_path.parent.relative_to(self.raw_dir)
                )
                category_folder.mkdir(parents=True, exist_ok=True)
                output_file = category_folder / f"{file_path.stem}.md"
                output_file.write_text(markdown, encoding="utf-8")

                parsed_doc = ParsedDocument(
                    raw_path=file_path,
                    markdown_path=output_file,
                    markdown=markdown,
                    metadata=metadata,
                )
                parsed_documents.append(parsed_doc)

                # 4. Chunk document
                chunks = self.chunker.split(markdown, metadata)
                if not chunks:
                    print(
                        f"No chunks produced for document: {file_path.name}"
                    )
                    continue

                print(
                    f"Generated {len(chunks)} chunks for {file_path.name}"
                )

                # 5. Clean up old indexes for this document (to support re-indexing updates)
                self.vector_store.delete_document(document_id)

                # 6. Generate embeddings and save to vector store
                # Batched at size 50 to avoid API rate limits or payload size failures
                chunk_texts = [c.text for c in chunks]
                embeddings = []
                batch_size = 50
                for i in range(0, len(chunk_texts), batch_size):
                    batch = chunk_texts[i : i + batch_size]
                    batch_embeddings = self.embedder.embed_documents(batch)
                    embeddings.extend(batch_embeddings)

                self.vector_store.add_chunks(chunks, embeddings)
                print(f"Successfully indexed: {file_path.name}")

            except Exception as e:
                print(
                    f"Error processing {file_path.name}: {e}",
                    file=sys.stderr,
                )

        # 7. Rebuild BM25 index if retriever exists
        try:
            from app.retrieval.bm25_retriever import BM25Retriever

            print("Rebuilding BM25 index...")
            bm25_retriever = BM25Retriever()
            bm25_retriever.rebuild_index()
            print("BM25 index rebuilt successfully.")
        except ImportError:
            print(
                "BM25Retriever not available yet. BM25 index rebuild skipped."
            )
        except Exception as e:
            print(
                f"Failed to rebuild BM25 index: {e}",
                file=sys.stderr,
            )

        return parsed_documents


def main():
    parser = argparse.ArgumentParser(
        description="Ingest enterprise documents."
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Path to raw documents directory",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild index by deleting existing database first",
    )
    args = parser.parse_args()

    # Update raw data directory path if source provided
    if args.source:
        settings.RAW_DATA_DIR = Path(args.source)

    pipeline = IngestionPipeline()

    if args.rebuild:
        print("Rebuild flag provided. Clearing existing collections...")
        try:
            pipeline.vector_store.client.delete_collection(
                "enterprise_documents"
            )
            # Recreate empty collection
            pipeline.vector_store.collection = (
                pipeline.vector_store.client.get_or_create_collection(
                    name="enterprise_documents",
                    metadata={"hnsw:space": "cosine"},
                )
            )
            print("Vector store cleared.")
        except Exception as e:
            print(f"Error clearing vector store: {e}")

    pipeline.ingest(rebuild=args.rebuild)


if __name__ == "__main__":
    main()