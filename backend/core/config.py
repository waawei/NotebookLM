"""
Application configuration.
"""

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODELING_WORKSPACE_ROOT = str(PROJECT_ROOT.parent / "NotebookLM-modeling-projects")


class Settings(BaseSettings):
    """Environment-backed application settings."""

    APP_NAME: str = "NotebookLM Clone"
    DEBUG: bool = True

    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    VECTOR_DB_PATH: str = "./data/chroma_db"
    VECTOR_DB_TYPE: str = "chroma"

    EMBEDDING_MODEL: str = "paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DEVICE: str = "cpu"

    LLM_PROVIDER: str = "ollama"
    LLM_MODEL: str = "qwen3:8b"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "http://localhost:11434"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2000

    UPLOAD_DIR: str = "./data/uploads"
    MODELING_WORKSPACE_ROOT: str = DEFAULT_MODELING_WORKSPACE_ROOT
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    MAX_FILE_SIZE: int = 10 * 1024 * 1024

    TOP_K_RESULTS: int = 5
    ENABLE_QUERY_REWRITE: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
