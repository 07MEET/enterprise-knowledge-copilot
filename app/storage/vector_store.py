from chromadb import PersistentClient

from app.config.settings import settings


class VectorStore:
    """
    ChromaDB vector store.
    """

    def __init__(self):

        self.client = PersistentClient(
            path=str(settings.VECTOR_STORE_DIR)
        )

        self.collection = self.client.get_or_create_collection(
            name="enterprise_documents"
        )