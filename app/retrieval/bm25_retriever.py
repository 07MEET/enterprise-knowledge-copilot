import os
import pickle
from app.config.settings import settings
from app.models.document_models import Chunk, RetrievedChunk
from app.storage.vector_store import VectorStore
from rank_bm25 import BM25Okapi


def tokenize(text: str) -> list[str]:
    """
    Simple whitespace and punctuation-stripping tokenizer for BM25.
    """
    if not text:
        return []
    return [word.lower().strip(".,!?;:()[]\"'") for word in text.split()]


class BM25Retriever:
    """
    Sparse retriever using the BM25 algorithm.
    """

    def __init__(self):
        """
        Initialize index path and attempt to load BM25 index from disk.
        """
        self.index_path = settings.VECTOR_STORE_DIR / "bm25_index.pkl"
        self.chunks: list[Chunk] = []
        self.bm25: BM25Okapi | None = None
        self.load_index()

    def load_index(self) -> None:
        """
        Load the serialized BM25 index and chunk mapping from disk.
        """
        if not self.index_path.exists():
            return

        try:
            with open(self.index_path, "rb") as f:
                data = pickle.load(f)
                self.chunks = data.get("chunks", [])
                self.bm25 = data.get("bm25")
        except Exception as e:
            print(f"Failed to load BM25 index: {e}")

    def save_index(self) -> None:
        """
        Save the BM25 index and chunk mapping to disk.
        """
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.index_path, "wb") as f:
                pickle.dump(
                    {
                        "chunks": self.chunks,
                        "bm25": self.bm25,
                    },
                    f,
                )
        except Exception as e:
            print(f"Failed to save BM25 index: {e}")

    def rebuild_index(self) -> None:
        """
        Fetch all chunks from ChromaDB and rebuild the BM25 index.
        """
        vector_store = VectorStore()

        # Fetch all records from ChromaDB collection
        results = vector_store.collection.get(
            include=["documents", "metadatas"]
        )

        if not results or not results["ids"]:
            self.chunks = []
            self.bm25 = None
            # Clean up pickle file if database is empty
            if self.index_path.exists():
                os.remove(self.index_path)
            return

        ids = results["ids"]
        documents = results["documents"]
        metadatas = results["metadatas"]

        self.chunks = []
        tokenized_corpus = []

        for i in range(len(ids)):
            chunk = Chunk(
                chunk_id=ids[i],
                text=documents[i],
                metadata=metadatas[i] or {},
            )
            self.chunks.append(chunk)
            tokenized_corpus.append(tokenize(chunk.text))

        if tokenized_corpus:
            self.bm25 = BM25Okapi(tokenized_corpus)
            self.save_index()
            print(f"BM25 index updated with {len(self.chunks)} chunks.")

    def search(
        self,
        query: str,
        k: int = 5,
    ) -> list[RetrievedChunk]:
        """
        Search the BM25 index for keyword matches.
        """
        if not self.bm25 or not self.chunks:
            return []

        tokenized_query = tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)

        # Sort index positions based on score in descending order
        ranked_indices = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True,
        )[:k]

        retrieved_chunks = []
        for idx, score in ranked_indices:
            chunk = self.chunks[idx]
            retrieved_chunks.append(
                RetrievedChunk(
                    chunk=chunk,
                    score=float(score),
                    retrieval_method="sparse",
                )
            )

        return retrieved_chunks
