"""
Core Configuration – loads from environment variables via pydantic-settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Wakili"
    APP_ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Security
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALLOWED_ORIGINS: List[str] = [

        "https://wakili-kohl.vercel.app",
        "https://wakili-dn2nsm23k-mungaimwangi001s-projects.vercel.app",
        "http://localhost:3000",
        "http://localhost:8080",
    ]

    # Database
    DATABASE_URL: str

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "/app/chroma_data"
    CHROMA_COLLECTION_NAME: str = "wakili_documents"
    KB_COLLECTION_NAME: str = "wakili_knowledge_base"

    # Redis
    REDIS_URL: str

    REDIS_TTL_SECONDS: int = 3600

    # Embedding
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_CACHE_DIR: str = "/app/.model_cache"

    # Groq
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # LLM generation
    LLM_MAX_NEW_TOKENS: int = 1024
    LLM_TEMPERATURE: float = 0.3

    # RAG
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 100
    TOP_K_RETRIEVAL: int = 5
    MAX_CONTEXT_TOKENS: int = 2048
    CONFIDENCE_THRESHOLD: float = 0.20

    # Conversation memory
    MAX_HISTORY_TURNS: int = 10

    # File Upload
    UPLOAD_DIR: str = "/app/uploads"
    MAX_FILE_SIZE_MB: int = 20
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "docx", "txt", "png", "jpg", "jpeg"]

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60

    @property
    def TOP_K_CHUNKS(self) -> int:
        return self.TOP_K_RETRIEVAL

    @property
    def CHROMA_COLLECTION(self) -> str:
        return self.CHROMA_COLLECTION_NAME

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
