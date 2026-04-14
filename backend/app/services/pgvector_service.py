"""
PGVector Knowledge Base Service
Stores and retrieves KB embeddings in PostgreSQL — zero extra cost on Render.
"""
from __future__ import annotations
import structlog
from typing import List, Tuple
from sqlalchemy import text
from app.core.database import async_engine

log = structlog.get_logger()

# ── Schema ────────────────────────────────────────────────────────────────────

CREATE_EXTENSION_SQL = "CREATE EXTENSION IF NOT EXISTS vector;"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS knowledge_base (
    id          SERIAL PRIMARY KEY,
    source      TEXT NOT NULL,
    content     TEXT NOT NULL,
    embedding   vector(384)          -- all-MiniLM-L6-v2 outputs 384 dims
);
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS kb_embedding_idx
ON knowledge_base USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 10);
"""

# ── Built-in Kenyan Law KB ────────────────────────────────────────────────────

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


# ── Setup ─────────────────────────────────────────────────────────────────────

async def setup_pgvector_kb() -> None:
    """
    Creates the table and seeds KB rows if empty.
    Called once at startup — cheap because it's just SQL, no model loaded yet.
    """
    async with async_engine.begin() as conn:
        await conn.execute(text(CREATE_EXTENSION_SQL))
        await conn.execute(text(CREATE_TABLE_SQL))
        try:
            await conn.execute(text(CREATE_INDEX_SQL))
        except Exception:
            pass  # index may already exist

        result = await conn.execute(text("SELECT COUNT(*) FROM knowledge_base"))
        count = result.scalar()

    if count and count > 0:
        log.info("KB already seeded in PostgreSQL", chunks=count)
        return

    log.info("Seeding knowledge base into PostgreSQL (lazy embeddings)...")
    # Store text only — embeddings are generated lazily on first query
    async with async_engine.begin() as conn:
        for entry in BUILT_IN_KB:
            await conn.execute(
                text(
                    "INSERT INTO knowledge_base (source, content) VALUES (:source, :content)"
                ),
                {"source": entry["source"], "content": entry["text"]},
            )
    log.info("✅ KB rows inserted (embeddings will be computed on first query)", chunks=len(BUILT_IN_KB))


async def ensure_embeddings_exist() -> None:
    """
    Generates and stores embeddings for any KB row that has none.
    Called lazily on the first real /ask request — not at startup.
    """
    async with async_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT COUNT(*) FROM knowledge_base WHERE embedding IS NULL")
        )
        missing = result.scalar()

    if not missing:
        return

    log.info("Computing KB embeddings (first-time lazy init)...", missing=missing)

    # Only import heavy model here — never at startup
    from app.services.embedding_service import EmbeddingService
    embedder = EmbeddingService.get_instance()

    async with async_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT id, content FROM knowledge_base WHERE embedding IS NULL")
        )
        rows = result.fetchall()

    for row in rows:
        vec = embedder.embed_single(row.content)
        async with async_engine.begin() as conn:
            await conn.execute(
                text("UPDATE knowledge_base SET embedding = :vec WHERE id = :id"),
                {"vec": str(vec), "id": row.id},
            )

    log.info("✅ KB embeddings ready")


async def search_kb(query: str, top_k: int = 5) -> List[Tuple[str, str, float]]:
    """
    Returns top_k results as list of (source, content, similarity_score).
    Triggers lazy embedding generation if needed.
    """
    await ensure_embeddings_exist()

    from app.services.embedding_service import EmbeddingService
    embedder = EmbeddingService.get_instance()
    query_vec = embedder.embed_single(query)

    async with async_engine.connect() as conn:
        result = await conn.execute(
            text("""
                SELECT source, content,
                       1 - (embedding <=> :vec) AS similarity
                FROM knowledge_base
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> :vec
                LIMIT :k
            """),
            {"vec": str(query_vec), "k": top_k},
        )
        rows = result.fetchall()

    return [(r.source, r.content, float(r.similarity)) for r in rows]