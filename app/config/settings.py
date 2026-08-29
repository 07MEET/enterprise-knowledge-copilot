import os
from pathlib import Path

# Prevent OpenMP DLL collision crashes on Windows when PyTorch and ONNX/ChromaDB load together
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    # ==========================
    # Application
    # ==========================
    APP_NAME: str = "Enterprise Knowledge Copilot"

    # ==========================
    # Data Directories
    # ==========================
    RAW_DATA_DIR: Path = Path("data/raw")
    PROCESSED_DATA_DIR: Path = Path("data/processed")
    VECTOR_STORE_DIR: Path = Path("data/vector_store")

    # ==========================
    # Chunking
    # ==========================
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150

    # ==========================
    # LLM Provider
    # ==========================
    # Options: "openrouter" | "local" | "gemini"
    LLM_PROVIDER: str = "local"

    # OpenRouter (recommended — access any model via one API key)
    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_MODEL: str = "openrouter/free"
    # Set to a specific model to override free auto-routing, e.g.:
    # "meta-llama/llama-3.2-3b-instruct:free" or "meta-llama/llama-3.3-70b-instruct:free"

    # Google Gemini (optional fallback)
    GEMINI_API_KEY: str | None = None

    # Local Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Model name used for local/gemini providers
    LLM_MODEL: str = "qwen2.5:7b"

    # Embedding model (always local — not affected by LLM_PROVIDER)
    EMBEDDING_MODEL: str = "BAAI/bge-large-en-v1.5"

    @property
    def USE_LOCAL(self) -> bool:
        """Backward-compat property: True when running against local Ollama."""
        return self.LLM_PROVIDER.lower() == "local"

    def model_post_init(self, __context: object) -> None:
        """
        Auto-detect provider from available API keys if LLM_PROVIDER
        is still at its default value ("local").

        Priority: OpenRouter > Gemini > Local (Ollama)
        This means you only need to set the API key — not LLM_PROVIDER too.
        """
        if self.LLM_PROVIDER == "local":
            if self.OPENROUTER_API_KEY:
                object.__setattr__(self, "LLM_PROVIDER", "openrouter")
            elif self.GEMINI_API_KEY:
                object.__setattr__(self, "LLM_PROVIDER", "gemini")
        print(f"[LLM] Provider: {self.LLM_PROVIDER} | Model: {self.OPENROUTER_MODEL if self.LLM_PROVIDER == 'openrouter' else self.LLM_MODEL}")


settings = Settings()