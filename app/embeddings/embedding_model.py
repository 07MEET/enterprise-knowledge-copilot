from google import genai

from app.config.settings import settings


class EmbeddingModel:
    """
    Generates embeddings using Gemini.
    """

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        embeddings = []

        for text in texts:

            response = self.client.models.embed_content(
                model=settings.EMBEDDING_MODEL,
                contents=text,
            )

            embeddings.append(
                response.embeddings[0].values
            )

        return embeddings

    def embed_query(
        self,
        query: str,
    ) -> list[float]:

        response = self.client.models.embed_content(
            model=settings.EMBEDDING_MODEL,
            contents=query,
        )

        return response.embeddings[0].values