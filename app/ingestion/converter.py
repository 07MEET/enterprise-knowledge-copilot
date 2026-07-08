from langchain_core.documents import Document

from app.models.document_models import ParsedDocument


def to_langchain_document(
    parsed_document: ParsedDocument,
) -> Document:
    """
    Convert ParsedDocument to LangChain Document.
    """

    return Document(
        page_content=parsed_document.markdown,
        metadata=parsed_document.metadata,
    )