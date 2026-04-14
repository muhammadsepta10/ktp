from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ocr_db"

    # OCR Configuration
    OCR_LANGUAGE: str = "en"
    OCR_USE_GPU: bool = False
    OCR_MAX_IMAGE_SIZE: int = 1920

    # AI Model Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:14b"
    OLLAMA_TIMEOUT: int = 120  # timeout dalam detik
    AI_MAX_RETRIES: int = 2  # jumlah retry jika validasi gagal

    # Upload Configuration
    UPLOAD_DIR: str = "./uploads"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
