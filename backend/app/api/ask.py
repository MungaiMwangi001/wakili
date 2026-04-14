"""
Q&A endpoint – POST /ask
Runs the RAG pipeline with conversation memory and returns a structured legal answer.
"""
import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.query import Query
from app.schemas.ask import AskRequest, AskResponse, RetrievedChunk
from app.utils.auth_deps import get_current_user
from app.services.rag_pipeline import run_rag_query

log = structlog.get_logger()
router = APIRouter()


def _chunk_to_dict(c) -> dict:
    """
    Convert any chunk representation to a plain dict so Pydantic
    can validate it cleanly.
    """
    if isinstance(c, dict):
        return c
    # Pydantic v2
    if hasattr(c, "model_dump"):
        return c.model_dump()
    # Pydantic v1
    if hasattr(c, "dict"):
        return c.dict()
    # Dataclass or plain object with __dict__
    if hasattr(c, "__dict__"):
        return c.__dict__
    raise ValueError(f"Cannot convert chunk of type {type(c)} to dict")


@router.post("/ask", response_model=AskResponse)
async def ask_question(
    data: AskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Ask a legal question. Supports follow-up questions via conversation_history.
    Integrates with pgvector-backed knowledge base for memory efficiency.
    """
    # 1. Get all ready documents for this user
    result = await db.execute(
        select(Document).where(
            Document.user_id == current_user.id,
            Document.status == "ready",
        )
    )
    docs = result.scalars().all()

    # Note: We now allow queries even without docs because we have the built-in KB
    doc_ids = [d.id for d in docs]
    doc_titles = {d.id: d.title for d in docs}

    # 2. Verify specific document access if requested
    if data.document_id:
        if data.document_id not in doc_ids:
            raise HTTPException(status_code=404, detail="Document not found or not ready")

    # 3. Convert history to plain dicts for the pipeline
    history = [{"role": m.role, "content": m.content} for m in data.conversation_history]

    log.info("Running RAG pipeline", user_id=current_user.id, question=data.question)

    # 4. Run RAG pipeline
    # The pipeline internally should now use search_kb from pgvector_service
    try:
        rag_result = await run_rag_query(
            question=data.question,
            document_ids=doc_ids,
            document_titles=doc_titles,
            language=data.language,
            document_id=data.document_id,
            conversation_history=history,
        )
    except Exception as e:
        log.error("RAG pipeline failed", error=str(e))
        raise HTTPException(status_code=500, detail="Error processing your request")

    # 5. Log query for analytics
    query_record = Query(
        user_id=current_user.id,
        document_id=data.document_id,
        question=data.question,
        answer=rag_result["answer"],
        language=rag_result["language"],
        retrieved_chunks=rag_result["retrieved_chunks"],
        response_time_ms=rag_result["response_time_ms"],
    )
    db.add(query_record)
    await db.commit() # Using commit() to ensure record is saved

    # 6. Format chunks for response
    # We convert to dict first to avoid Pydantic validation issues
    chunk_dicts = [_chunk_to_dict(c) for c in rag_result["retrieved_chunks"]]
    chunks = [RetrievedChunk(**d) for d in chunk_dicts]

    return AskResponse(
        answer=rag_result["answer"],
        language=rag_result["language"],
        retrieved_chunks=chunks,
        clause_summaries=rag_result.get("clause_summaries", []),
        risk_flags=rag_result.get("risk_flags", []),
        obligations=rag_result.get("obligations", []),
        used_knowledge_base=rag_result.get("used_knowledge_base", False),
        disclaimer=rag_result.get("disclaimer", "This information is for guidance only."),
        response_time_ms=rag_result["response_time_ms"],
    )