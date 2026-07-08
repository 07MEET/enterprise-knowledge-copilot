from app.config.settings import settings
from app.embeddings.gemini import GeminiEmbeddingModel


def get_embedding_model():
    """
    Returns the configured embedding model.
    """

    if settings.EMBEDDING_MODEL.startswith("models/"):
        return GeminiEmbeddingModel()

    raise ValueError(
        f"Unsupported embedding model: {settings.EMBEDDING_MODEL}"
    )