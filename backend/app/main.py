"""
Wakili – RAG-powered Legal Document Analyzer
FastAPI Application Entry Point
"""
import json
import re
import structlog
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
from app.services.groq_service import get_groq_service
from app.services.pgvector_service import setup_pgvector_kb

log = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Wakili starting up...")

    # 1. DB tables (fast — just DDL)
    await create_tables()

    # 2. Seed KB rows into Postgres — NO model loaded, just SQL inserts
    await setup_pgvector_kb()

    # 3. Groq client (just an HTTP client, very cheap)
    get_groq_service()
    log.info(" Groq client ready", model=settings.GROQ_MODEL)

    #  Embedding model is NOT loaded here — lazy on first /ask request
    log.info(" Wakili ready — all systems go (embedding model loads on first request)")
    yield
    log.info("Wakili shutting down...")


app = FastAPI(
    title="Wakili API",
    description="RAG-powered Kenyan legal document analyzer",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
raw_origins = settings.ALLOWED_ORIGINS
origins = []
if isinstance(raw_origins, str):
    try:
        origins = json.loads(raw_origins)
    except json.JSONDecodeError:
        origins = [o.strip() for o in raw_origins.split(",") if o]
else:
    origins = raw_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://wakili-.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(GZipMiddleware, minimum_size=500)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,      prefix="/auth",      tags=["Authentication"])
app.include_router(documents.router)
app.include_router(ask.router,       prefix="",           tags=["Q&A"])
app.include_router(metrics.router,                        tags=["Metrics"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "wakili-api", "model": settings.GROQ_MODEL}