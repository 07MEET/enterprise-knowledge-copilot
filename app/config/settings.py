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
    # Gemini
    # ==========================
    GEMINI_API_KEY: str

    EMBEDDING_MODEL: str = "models/gemini-embedding-2"

    LLM_MODEL: str = "models/gemini-3.5-flash"


settings = Settings()