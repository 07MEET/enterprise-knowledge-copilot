from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Enterprise Knowledge Copilot"
    VERSION: str = "1.0.0"

    GEMINI_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()