from abc import ABC, abstractmethod


class BaseEmbeddingModel(ABC):
    """
    Base interface for embedding providers.
    """

    @abstractmethod
    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.
        """
        pass

    @abstractmethod
    def embed_query(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate embedding for a query.
        """
        pass