"""
Wakili – RAG-powered Legal Document Analyzer
FastAPI Application Entry Point
"""
import structlog
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import create_tables
from app.api import auth, documents, ask, metrics
from app.services.embedding_service import EmbeddingService
from app.services.groq_service import get_groq_service

log = structlog.get_logger()

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Wakili starting up...")
    await create_tables()

    # Pre-load embedding model — eliminates ~3s delay on first user request
    log.info("Loading embedding model...")
    embedder = EmbeddingService.get_instance()
    # Run a dummy embed so the model weights are fully loaded into memory
    embedder.embed_single("warmup")
    log.info("✅ Embedding model ready")

    # Validate Groq API key at startup so we fail fast if it's missing/wrong
    get_groq_service()
    log.info("✅ Groq client ready", model=settings.GROQ_MODEL)

    log.info("✅ Wakili ready — all systems go")
    yield
    log.info("👋 Wakili shutting down...")


app = FastAPI(
    title="Wakili API",
    description="RAG-powered Kenyan legal document analyzer",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS Configuration Fix ────────────────────────────────────────────────────
# This logic ensures that if ALLOWED_ORIGINS is a string like '["http://..."]', 
# it gets converted into a real Python list that CORSMiddleware understands.
raw_origins = settings.ALLOWED_ORIGINS
origins = []

if isinstance(raw_origins, str):
    try:
        # Try to parse if it's a JSON string like '["a", "b"]'
        origins = json.loads(raw_origins)
    except json.JSONDecodeError:
        # Fallback to comma-separated if it's not JSON
        origins = [o.strip() for o in raw_origins.split(",") if o]
else:
    origins = raw_origins

# ── Middleware ────────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# GZip compresses API responses — cuts payload size ~70% for large answers
app.add_middleware(GZipMiddleware, minimum_size=500)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,      prefix="/auth",      tags=["Authentication"])
app.include_router(documents.router)
app.include_router(ask.router,       prefix="",           tags=["Q&A"])
app.include_router(metrics.router,    tags=["Metrics"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "wakili-api", "model": settings.GROQ_MODEL}