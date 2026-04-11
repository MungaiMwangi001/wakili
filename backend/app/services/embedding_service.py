"""
Embedding Service – Singleton wrapper around sentence-transformers.
Uses all-MiniLM-L6-v2: free, local, no API key needed.
384-dimensional embeddings, fast on CPU.
"""
import structlog
from sentence_transformers import SentenceTransformer
from app.core.config import settings

log = structlog.get_logger()


class EmbeddingService:
    """Singleton that holds the loaded embedding model in memory."""
    _instance: "EmbeddingService | None" = None
    _model: SentenceTransformer | None = None

    @classmethod
    def get_instance(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if EmbeddingService._model is None:
            log.info("Loading embedding model", model=settings.EMBEDDING_MODEL)
            EmbeddingService._model = SentenceTransformer(
                settings.EMBEDDING_MODEL,
                cache_folder=settings.EMBEDDING_CACHE_DIR,
            )
            log.info("Embedding model loaded ✅")

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of text strings."""
        if not texts:
            return []
        embeddings = EmbeddingService._model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return embeddings.tolist()

    def embed_single(self, text: str) -> list[float]:
        """Embed a single string."""
        return self.embed([text])[0]
