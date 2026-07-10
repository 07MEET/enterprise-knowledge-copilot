from app.config.settings import settings
from app.embeddings.gemini import GeminiEmbeddingModel


_model_instance = None


def get_embedding_model():
    """
    Returns the configured embedding model (as a singleton).
    """
    global _model_instance
    if _model_instance is not None:
        return _model_instance

    if settings.USE_LOCAL:
        from app.embeddings.local import LocalEmbeddingModel
        _model_instance = LocalEmbeddingModel()
        return _model_instance

    if settings.EMBEDDING_MODEL.startswith("models/"):
        _model_instance = GeminiEmbeddingModel()
        return _model_instance

    raise ValueError(
        f"Unsupported embedding model: {settings.EMBEDDING_MODEL}"
    )