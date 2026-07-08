from chromadb import PersistentClient

from app.config.settings import settings
from app.models.document_models import Chunk, RetrievedChunk


class VectorStore:
    """
    ChromaDB vector store.
    """

    def __init__(self):
        """
        Initialize the ChromaDB persistent client and collection.
        """
        self.client = PersistentClient(
            path=str(settings.VECTOR_STORE_DIR)
        )

        # Configure collection to use Cosine similarity space
        self.collection = self.client.get_or_create_collection(
            name="enterprise_documents",
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
    ) -> None:
        """
        Add chunks and their corresponding embeddings to the vector store.
        """
        if not chunks:
            return

        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]

        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

    def delete_document(self, document_id: str) -> None:
        """
        Delete all chunks associated with a given document_id.
        Useful for cleaning up old indices before re-indexing.
        """
        self.collection.delete(
            where={"document_id": document_id}
        )

    def similarity_search(
        self,
        query_embedding: list[float],
        k: int = 5,
        where: dict | None = None,
    ) -> list[RetrievedChunk]:
        """
        Retrieve chunks similar to the query embedding.
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where,
        )

        retrieved_chunks = []
        if not results or not results["ids"] or not results["ids"][0]:
            return retrieved_chunks

        # Extract elements for the first query embedding
        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for i in range(len(ids)):
            # Cosine similarity score = 1.0 - Cosine distance
            score = 1.0 - distances[i]

            chunk = Chunk(
                chunk_id=ids[i],
                text=documents[i],
                metadata=metadatas[i],
            )
            retrieved_chunks.append(
                RetrievedChunk(
                    chunk=chunk,
                    score=score,
                    retrieval_method="dense",
                )
            )

        return retrieved_chunks