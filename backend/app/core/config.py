"""
Core Configuration – loads from environment variables via pydantic-settings.
"""
from pydantic_settings import BaseSettings
from typing import List

import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Wakili"
    APP_ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Security
    SECRET_KEY: str = "REMOVED_SECRET_KEY"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALLOWED_ORIGINS: List[str] = [
        "https://wakili-kohl.vercel.app",
        "http://localhost:3000",
        "http://localhost:8080",
    ]

    # Database
    DATABASE_URL: str = "postgresql://wakili_db_user:REMOVED_DB_PASS@dpg-d7cumfbeo5us7380nk4g-a.oregon-postgres.render.com/wakili_db"

    # ChromaDB
    # ChromaDB
    CHROMA_PERSIST_DIR: str = "/app/chroma_data"
    CHROMA_COLLECTION_NAME: str = "wakili_documents"
    KB_COLLECTION_NAME: str = "wakili_knowledge_base"

    # Redis
    REDIS_URL: str = "rediss://default:REMOVED_REDIS_PASS@trusting-ocelot-73157.upstash.io:6379"
    REDIS_TTL_SECONDS: int = 3600

    # Embedding
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_CACHE_DIR: str = "/app/.model_cache"

    # Groq
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # LLM generation
    LLM_MAX_NEW_TOKENS: int = 1024
    LLM_TEMPERATURE: float = 0.3

    # RAG
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 100
    TOP_K_RETRIEVAL: int = 5
    MAX_CONTEXT_TOKENS: int = 2048
    CONFIDENCE_THRESHOLD: float = 0.20   # below this → use knowledge base

    # Conversation memory
    MAX_HISTORY_TURNS: int = 10   # how many past Q+A pairs to send to Groq

    # File Upload
    UPLOAD_DIR: str = "/app/uploads"
    MAX_FILE_SIZE_MB: int = 20
    ALLOWED_EXTENSIONS: list[str] = ["pdf", "docx", "txt", "png", "jpg", "jpeg"]

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60

    @property
    def TOP_K_CHUNKS(self) -> int:
        return self.TOP_K_RETRIEVAL

    @property
    def CHROMA_COLLECTION(self) -> str:
        return self.CHROMA_COLLECTION_NAME

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


settings = Settings()