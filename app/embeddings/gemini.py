from google import genai

from app.config.settings import settings
from app.embeddings.base import BaseEmbeddingModel


class GeminiEmbeddingModel(BaseEmbeddingModel):
    """
    Gemini Embedding model implementation.
    """

    def __init__(self) -> None:
        """
        Initialize the Gemini embedding client.
        """
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )
        self.model = settings.EMBEDDING_MODEL

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.
        """
        if not texts:
            return []

        # Batch call to Gemini embed_content API
        response = self.client.models.embed_content(
            model=self.model,
            contents=texts,
        )

        return [emb.values for emb in response.embeddings]

    def embed_query(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate embedding for a query.
        """
        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
        )

        return response.embeddings[0].values
