"""
RAG Pipeline – orchestrates the full Retrieval-Augmented Generation flow.

Pipeline:
  1. Detect language (English / Swahili)
  2. Search BOTH built-in knowledge base AND user documents
  3. Merge and deduplicate results
  4. Build prompt with retrieved context + conversation history
  5. Generate answer via Groq API
  6. Append legal disclaimer
  7. Return structured JSON response
"""
import time
import structlog
from typing import List, Tuple, Dict, Any
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.embedding_service import EmbeddingService
from app.services.pgvector_service import search_kb
from app.services.groq_service import get_groq_service
from app.utils.language import detect_language
from app.core.config import settings
from app.core.database import AsyncSessionLocal

log = structlog.get_logger()

async def search_user_documents(
    question: str, 
    document_ids: List[int], 
    document_titles: Dict[int, str],
    top_k: int = 3
) -> List[Tuple[str, str, float]]:
    """
    Search user-uploaded documents using vector similarity.
    Returns list of (source, content, similarity_score)
    """
    if not document_ids:
        return []
    
    try:
        # Get embedding for the question
        embedder = EmbeddingService.get_instance()
        query_embedding = embedder.embed_single(question)
        
        # Search documents table for similar content
        async with AsyncSessionLocal() as db:
            # This assumes your documents table has an embedding column
            # If not, we'll search by keyword as fallback
            try:
                # Try vector search first
                result = await db.execute(
                    text("""
                        SELECT id, title, content, 
                               1 - (embedding <=> :embedding) as similarity
                        FROM documents
                        WHERE user_id = ANY(:user_ids)
                        AND status = 'ready'
                        AND embedding IS NOT NULL
                        ORDER BY embedding <=> :embedding
                        LIMIT :k
                    """),
                    {
                        "embedding": str(query_embedding),
                        "user_ids": document_ids,
                        "k": top_k
                    }
                )
                rows = result.fetchall()
                
                if rows:
                    return [(f"User Document: {row.title}", row.content, float(row.similarity)) 
                           for row in rows]
            except Exception as e:
                log.warning("Vector search failed, falling back to keyword search", error=str(e))
            
            # Fallback: Keyword search on document content
            # Build search conditions for each document ID
            doc_conditions = " OR ".join([f"id = {doc_id}" for doc_id in document_ids[:5]])
            if doc_conditions:
                result = await db.execute(
                    text(f"""
                        SELECT id, title, content
                        FROM documents
                        WHERE ({doc_conditions})
                        AND status = 'ready'
                        AND content IS NOT NULL
                        LIMIT :k
                    """),
                    {"k": top_k}
                )
                rows = result.fetchall()
                
                if rows:
                    # Simple keyword relevance scoring
                    question_words = set(question.lower().split())
                    scored_results = []
                    for row in rows:
                        content_lower = row.content.lower()
                        score = sum(1 for word in question_words if word in content_lower) / max(len(question_words), 1)
                        if score > 0:
                            scored_results.append((f"User Document: {row.title}", row.content, score))
                    
                    scored_results.sort(key=lambda x: x[2], reverse=True)
                    return scored_results[:top_k]
    
    except Exception as e:
        log.error("Error searching user documents", error=str(e))
    
    return []


async def get_available_document_titles(db: AsyncSession, document_ids: List[int]) -> List[str]:
    """Get list of available document titles for better error messages"""
    if not document_ids:
        return []
    
    try:
        result = await db.execute(
            select(Document.title).where(Document.id.in_(document_ids), Document.status == "ready")
        )
        return [row[0] for row in result.all()]
    except:
        return []


async def run_rag_query(
    question: str,
    document_ids: list[int],
    document_titles: dict[int, str],
    language: str | None = None,
    document_id: int | None = None,
    conversation_history: list = [],
    db: AsyncSession = None,
) -> dict:
    """Main RAG pipeline - searches both KB and user documents"""
    start_time = time.time()

    # 1. Language detection
    lang = language or detect_language(question)
    log.info("RAG query started", language=lang, has_user_docs=len(document_ids) > 0)

    # 2. Search BOTH sources
    all_chunks = []
    
    # Search built-in knowledge base
    kb_chunks = await search_kb(question, top_k=settings.TOP_K_RETRIEVAL)
    all_chunks.extend(kb_chunks)
    log.info(f"Found {len(kb_chunks)} chunks from knowledge base")
    
    # Search user documents if any exist
    if document_ids:
        user_chunks = await search_user_documents(question, document_ids, document_titles, top_k=3)
        all_chunks.extend(user_chunks)
        log.info(f"Found {len(user_chunks)} chunks from user documents")
    
    # 3. Deduplicate by content (keep highest score for similar content)
    unique_chunks = {}
    for source, content, score in all_chunks:
        # Use first 200 chars as key for deduplication
        content_key = content[:200].strip()
        if content_key not in unique_chunks or unique_chunks[content_key][2] < score:
            unique_chunks[content_key] = (source, content, score)
    
    final_chunks = list(unique_chunks.values())
    final_chunks.sort(key=lambda x: x[2], reverse=True)  # Sort by score
    
    used_knowledge_base = len(final_chunks) > 0

    # 4. If no results, return helpful message with available documents
    if not final_chunks:
        # Get list of available documents if db session provided
        available_docs = []
        if db and document_ids:
            available_docs = await get_available_document_titles(db, document_ids)
        
        no_result_msg = (
            f"Samahani, sikupata taarifa husika kuhusu '{question}'." if lang == "sw"
            else f"Sorry, I could not find relevant information about '{question}' in the legal knowledge base."
        )
        
        if available_docs:
            no_result_msg += f"\n\nYour uploaded documents: {', '.join(available_docs[:5])}\nPlease try asking about the content of these specific documents."
        else:
            no_result_msg += "\n\nTry rephrasing your question or asking about Kenyan employment law, contract law, or consumer protection."
        
        return {
            "answer": no_result_msg,
            "language": lang,
            "retrieved_chunks": [],
            "clause_summaries": [],
            "risk_flags": [],
            "obligations": [],
            "used_knowledge_base": False,
            "disclaimer": "This information is for guidance only.",
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    # 5. Build context from retrieved chunks
    retrieved_chunks = []
    context_parts = []
    
    # Limit to top K chunks to avoid token limits
    top_chunks = final_chunks[:settings.TOP_K_RETRIEVAL]
    
    for source, content, score in top_chunks:
        retrieved_chunks.append({
            "text": content[:500],  # Limit chunk size
            "document_id": 0,
            "document_title": source,
            "chunk_index": 0,
            "relevance_score": round(score, 3),
            "clause_number": None,
            "page_number": None
        })
        context_parts.append(f"[Source: {source} (relevance: {score:.2f})]\n{content[:800]}")

    context = "\n\n---\n\n".join(context_parts)

    # 6. Generate answer via Groq
    groq = get_groq_service()
    
    # Enhance prompt with document context
    enhanced_question = question
    if document_id and document_titles.get(document_id):
        enhanced_question = f"Regarding the document '{document_titles[document_id]}': {question}"
    
    try:
        result = groq.ask(
            question=enhanced_question,
            context=context,
            language=lang,
            history=conversation_history,
            used_knowledge_base=used_knowledge_base,
        )
    except Exception as e:
        log.error("Groq API failed", error=str(e))
        return {
            "answer": "I'm having trouble generating an answer right now. Please try again in a moment.",
            "language": lang,
            "retrieved_chunks": retrieved_chunks,
            "clause_summaries": [],
            "risk_flags": [],
            "obligations": [],
            "used_knowledge_base": used_knowledge_base,
            "disclaimer": "Service temporarily unavailable.",
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    elapsed_ms = round((time.time() - start_time) * 1000, 2)
    
    # 7. Handle disclaimer split
    answer_text = result.get("answer", "")
    disclaimer = ""
    if "---" in answer_text:
        parts = answer_text.rsplit("---", 1)
        answer_text = parts[0].strip()
        disclaimer = parts[1].strip().lstrip("*").rstrip("*").strip()

    return {
        "answer": answer_text,
        "language": lang,
        "retrieved_chunks": retrieved_chunks,
        "clause_summaries": result.get("clause_summaries", []),
        "risk_flags": result.get("risk_flags", []),
        "obligations": result.get("obligations", []),
        "used_knowledge_base": used_knowledge_base,
        "disclaimer": disclaimer or "This information is for guidance only. Consult a qualified lawyer for legal advice.",
        "response_time_ms": elapsed_ms,
    }