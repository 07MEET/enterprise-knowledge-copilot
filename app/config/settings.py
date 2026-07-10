from pathlib import Path

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
    # Gemini / Local Models
    # ==========================
    GEMINI_API_KEY: str | None = None
    USE_LOCAL: bool = True
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    EMBEDDING_MODEL: str = "BAAI/bge-large-en-v1.5"

    LLM_MODEL: str = "llama3.2"


settings = Settings()