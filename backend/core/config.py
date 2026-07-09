"""
配置管理
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础配置
    APP_NAME: str = "NotebookLM Clone"
    DEBUG: bool = True

    # CORS 配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # 向量数据库配置
    VECTOR_DB_PATH: str = "./data/chroma_db"
    VECTOR_DB_TYPE: str = "chroma"  # chroma 或 qdrant

    # Embedding 模型配置
    EMBEDDING_MODEL: str = "paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DEVICE: str = "cpu"  # cpu 或 cuda

    # LLM 配置
    LLM_PROVIDER: str = "dashscope"  # dashscope(通义千问) 或 openai
    LLM_MODEL: str = "qwen-turbo"
    LLM_API_KEY: str = ""  # 从环境变量读取
    LLM_BASE_URL: str = ""  # 自定义 API 地址（可选）
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2000

    # 文档处理配置
    UPLOAD_DIR: str = "./data/uploads"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    # RAG 配置
    TOP_K_RESULTS: int = 5  # 检索返回的文档块数量

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
