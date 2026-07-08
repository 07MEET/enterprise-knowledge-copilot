import uuid

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from app.config.settings import settings
from app.models.document_models import Chunk


class Chunker:
    """
    Creates chunks from parsed markdown.
    """

    def __init__(self):

        self.header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "h1"),
                ("##", "h2"),
                ("###", "h3"),
            ]
        )

        self.recursive_splitter = (
            RecursiveCharacterTextSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
            )
        )

    def split(self, markdown: str, metadata: dict):

        chunks = []

        sections = self.header_splitter.split_text(markdown)

        for section in sections:
            # Merge document-level metadata with section headers (h1, h2, h3)
            combined_metadata = {**metadata, **section.metadata}

            documents = self.recursive_splitter.create_documents(
                [section.page_content],
                metadatas=[combined_metadata],
            )

            for document in documents:

                chunks.append(
                    Chunk(
                        chunk_id=str(uuid.uuid4()),
                        text=document.page_content,
                        metadata=document.metadata,
                    )
                )

        return chunks