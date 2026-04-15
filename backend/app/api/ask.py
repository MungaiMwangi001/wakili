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
    """Convert any chunk representation to a plain dict so Pydantic can validate it cleanly."""
    if isinstance(c, dict):
        return c
    if hasattr(c, "model_dump"):
        return c.model_dump()
    if hasattr(c, "dict"):
        return c.dict()
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

    doc_ids = [d.id for d in docs]
    doc_titles = {d.id: d.title for d in docs}

    # 2. Verify specific document access if requested
    if data.document_id:
        if data.document_id not in doc_ids:
            raise HTTPException(status_code=404, detail="Document not found or not ready")

    # 3. Convert history to plain dicts for the pipeline
    history = [{"role": m.role, "content": m.content} for m in data.conversation_history]

    log.info("Running RAG pipeline", 
             user_id=current_user.id, 
             question=data.question[:50],
             has_docs=len(doc_ids) > 0)

    # 4. Run RAG pipeline with db session for better error messages
    try:
        rag_result = await run_rag_query(
            question=data.question,
            document_ids=doc_ids,
            document_titles=doc_titles,
            language=data.language,
            document_id=data.document_id,
            conversation_history=history,
            db=db,  # Pass db for document title lookup
        )
    except Exception as e:
        log.error("RAG pipeline failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing your request: {str(e)}")

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
    await db.commit()

    # 6. Format chunks for response
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


@router.get("/ask/debug")
async def debug_rag(
    question: str = "What are payment obligations?",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Debug endpoint to test RAG retrieval without LLM generation"""
    from app.services.pgvector_service import search_kb
    
    # Test KB search
    kb_results = await search_kb(question, top_k=3)
    
    # Test user document search
    result = await db.execute(
        select(Document).where(
            Document.user_id == current_user.id,
            Document.status == "ready",
        )
    )
    docs = result.scalars().all()
    doc_ids = [d.id for d in docs]
    doc_titles = {d.id: d.title for d in docs}
    
    from app.services.rag_pipeline import search_user_documents
    user_results = await search_user_documents(question, doc_ids, doc_titles, top_k=3)
    
    return {
        "question": question,
        "kb_results": [{"source": s, "preview": c[:100], "score": sc} for s, c, sc in kb_results],
        "user_results": [{"source": s, "preview": c[:100], "score": sc} for s, c, sc in user_results],
        "total_results": len(kb_results) + len(user_results)
    }