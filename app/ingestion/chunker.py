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

    def split(self, markdown: str, metadata: dict, page_mapping: dict = None):

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
                # Resolve physical page numbers from page_mapping (handling page crossings)
                chunk_pages = set()
                if page_mapping:
                    chunk_text_stripped = document.page_content.strip()
                    # Try exact paragraph matching
                    for para_text, page_no in page_mapping.items():
                        if len(para_text) > 10 and para_text in chunk_text_stripped:
                            chunk_pages.add(page_no)
                    # Fallback to line overlap matching
                    lines = [l.strip() for l in document.page_content.split("\n") if len(l.strip()) > 40]
                    for line in lines:
                        for para_text, page_no in page_mapping.items():
                            if len(para_text) > 10 and (line in para_text or para_text in line):
                                chunk_pages.add(page_no)

                # Add page or page range to combined metadata
                doc_metadata = combined_metadata.copy()
                if chunk_pages:
                    sorted_pages = sorted(list(chunk_pages))
                    # A single chunk of 800 chars cannot span more than 2 pages.
                    # Spans larger than 2 pages are false positives from running headers/footers.
                    if len(sorted_pages) > 1 and (sorted_pages[-1] - sorted_pages[0] > 2):
                        sorted_pages = [sorted_pages[0]]

                    if len(sorted_pages) == 1:
                        doc_metadata["page"] = sorted_pages[0]
                    else:
                        doc_metadata["page"] = f"{sorted_pages[0]}-{sorted_pages[-1]}"

                chunks.append(
                    Chunk(
                        chunk_id=str(uuid.uuid4()),
                        text=document.page_content,
                        metadata=doc_metadata,
                    )
                )

        return chunks