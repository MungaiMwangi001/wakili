"""
Wakili – RAG-powered Legal Document Analyzer
FastAPI Application Entry Point
"""
import os
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

CHROMA_PERSIST_DIR = os.environ.get("CHROMA_PERSIST_DIR", "/app/chroma_data")


def _auto_load_knowledge_base():
    """Load the built-in Kenyan law KB into ChromaDB on first boot."""
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer

        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
        client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

        try:
            col = client.get_collection(settings.KB_COLLECTION_NAME)
            if col.count() > 0:
                log.info("Knowledge base already loaded", chunks=col.count())
                return
        except Exception:
            pass

        log.info("Loading knowledge base into ChromaDB...")

        BUILT_IN_KB = [
            {
                "source": "Employment Act 2007 – Kenya",
                "text": """The Employment Act 2007 of Kenya governs employment relationships.
Key provisions:
- Section 35: Termination requires notice. For monthly paid employees, minimum 28 days notice.
- Section 36: Summary dismissal is allowed only for gross misconduct such as theft, assault, or insubordination.
- Section 27: Maximum working hours are 52 per week, or 60 with overtime consent.
- Section 31: Employees are entitled to 21 days annual leave after 12 months of continuous service.
- Section 29: Maternity leave is 3 months (91 days) on full pay.
- Section 30: Paternity leave is 2 weeks.
- Wrongful termination: Employer must show valid reason and follow fair procedure.
- Redundancy: Employer must give 1 month notice, pay 15 days per year of service, and notify the Labour Officer.""",
            },
            {
                "source": "Contract Act Cap 23 – Kenya",
                "text": """The Law of Contract Act (Cap 23) governs contracts in Kenya.
Key provisions:
- A valid contract requires: offer, acceptance, consideration, capacity, and legality.
- Consideration must be adequate but need not be equal in value.
- Minors (under 18) lack capacity to contract except for necessities.
- A contract induced by misrepresentation, fraud, or undue influence is voidable.
- Penalty clauses that are punitive rather than compensatory may be struck down by courts.
- Liquidated damages clauses are enforceable if they represent a genuine pre-estimate of loss.
- Unlimited liability clauses may be challenged as unconscionable in consumer contracts.
- Force majeure clauses excuse performance when unforeseen events make performance impossible.""",
            },
            {
                "source": "Consumer Protection Act 2012 – Kenya",
                "text": """The Consumer Protection Act 2012 protects consumers in Kenya.
Key provisions:
- Section 55: Unfair contract terms are prohibited. A term is unfair if it causes significant imbalance.
- Section 56: Auto-renewal clauses must be clearly disclosed to consumers.
- Section 62: Consumers have the right to clear and plain language in contracts.
- Section 74: Suppliers cannot exclude liability for death or personal injury caused by negligence.
- Section 87: Consumers may rescind contracts entered into under false pretenses within 5 business days.""",
            },
            {
                "source": "Land Act 2012 – Kenya",
                "text": """The Land Act 2012 governs land transactions in Kenya.
Key provisions:
- All land in Kenya is vested in the National Government in trust for the Kenyan people.
- Section 79: Leases of more than 2 years must be in writing and registered.
- Section 90: A landlord must give 6 months notice before terminating a lease.
- Section 107: A purchaser of land must conduct due diligence including a search at the Land Registry.""",
            },
            {
                "source": "Common Kenyan Contract Risk Flags",
                "text": """Common risk flags in Kenyan contracts:
1. Unlimited liability clauses: May not be enforceable.
2. Termination ambiguity: Contracts without specified grounds give excessive power to one party.
3. Auto-renewal traps: Short notice windows may be unfair.
4. Unilateral variation: Clauses allowing one party to change terms without consent are a red flag.
5. Jurisdiction clauses: Foreign jurisdiction may disadvantage Kenyan parties.
6. Indemnification: Broad indemnity clauses are risky.
7. Non-compete clauses: Must be reasonable in scope, geography, and time.
8. Penalty clauses: Excessive penalties may be unenforceable under Cap 23.""",
            },
        ]

        model = SentenceTransformer(settings.EMBEDDING_MODEL)
        texts = [e["text"] for e in BUILT_IN_KB]
        embeddings = model.encode(texts, normalize_embeddings=True).tolist()

        collection = client.get_or_create_collection(
            name=settings.KB_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        collection.add(
            ids=[f"kb_builtin_{i}" for i in range(len(texts))],
            embeddings=embeddings,
            documents=texts,
            metadatas=[{"source": e["source"], "chunk_index": i} for i, e in enumerate(BUILT_IN_KB)],
        )
        log.info("✅ Knowledge base loaded", chunks=len(texts))

    except Exception as e:
        log.warning("KB auto-load failed — queries will use LLM only", error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Wakili starting up...")
    await create_tables()

    log.info("Loading embedding model...")
    embedder = EmbeddingService.get_instance()
    embedder.embed_single("warmup")
    log.info("✅ Embedding model ready")

    # Auto-load knowledge base on first boot
    _auto_load_knowledge_base()

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

# ── Middleware ────────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
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