from app.config.settings import settings
from app.embeddings.gemini import GeminiEmbeddingModel


_model_instance = None


def get_embedding_model():
    """
    Returns the configured embedding model (as a singleton).

    Embedding model selection is independent of LLM_PROVIDER:
    - Gemini embedding models start with "models/" (e.g. models/text-embedding-004)
    - Everything else uses the local sentence-transformers model
    """
    global _model_instance
    if _model_instance is not None:
        return _model_instance

    if settings.EMBEDDING_MODEL.startswith("models/"):
        # Gemini embedding model
        _model_instance = GeminiEmbeddingModel()
    else:
        # Local sentence-transformers model (default: BAAI/bge-large-en-v1.5)
        from app.embeddings.local import LocalEmbeddingModel
        _model_instance = LocalEmbeddingModel()

    return _model_instance