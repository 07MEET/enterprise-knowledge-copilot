from sentence_transformers import SentenceTransformer

from app.config.settings import settings
from app.embeddings.base import BaseEmbeddingModel


class LocalEmbeddingModel(BaseEmbeddingModel):
    """
    Local embedding model implementation using sentence-transformers loaded on CUDA GPU.
    """

    def __init__(self) -> None:
        """
        Initialize the local SentenceTransformer model.
        """
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL, device=device)

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.
        """
        if not texts:
            return []

        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_query(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate embedding for a query.
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
