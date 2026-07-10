from google import genai

from app.config.settings import settings
from app.embeddings.base import BaseEmbeddingModel
from app.utils.rate_limiter import call_with_retry


class GeminiEmbeddingModel(BaseEmbeddingModel):
    """
    Gemini Embedding model implementation with automatic rate-limit backoff.
    """

    def __init__(self) -> None:
        """
        Initialize the Gemini embedding client.
        """
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.EMBEDDING_MODEL

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts one-by-one with rate-limit retries.
        """
        if not texts:
            return []

        embeddings = []
        for text in texts:
            response = call_with_retry(
                self.client.models.embed_content,
                model=self.model,
                contents=text,
            )
            embeddings.append(response.embeddings[0].values)

        return embeddings

    def embed_query(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate embedding for a query with rate-limit retries.
        """
        response = call_with_retry(
            self.client.models.embed_content,
            model=self.model,
            contents=text,
        )

        return response.embeddings[0].values
