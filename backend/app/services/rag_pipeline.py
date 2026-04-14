"""
RAG Pipeline – orchestrates the full Retrieval-Augmented Generation flow.

Pipeline:
  1. Detect language (English / Swahili)
  2. Embed the question  (local, free – all-MiniLM-L6-v2)
  3. Retrieve top-k chunks from user documents (ChromaDB, local)
  4. Check confidence score — fall back to knowledge base if low
  5. Build prompt with retrieved context + conversation history
  6. Generate answer via Groq API  (free tier – Llama 3.3 70B)
  7. Append legal disclaimer
  8. Return structured JSON response
"""
"""
RAG Pipeline – Updated for pgvector and memory efficiency.
"""
import time
import structlog

from app.services.embedding_service import EmbeddingService
from app.services.pgvector_service import search_kb  # <--- NEW IMPORT
from app.services.groq_service import get_groq_service
from app.utils.language import detect_language
from app.core.config import settings

log = structlog.get_logger()

async def run_rag_query(
    question: str,
    document_ids: list[int],
    document_titles: dict[int, str],
    language: str | None = None,
    document_id: int | None = None,
    conversation_history: list = [],
) -> dict:
    start_time = time.time()

    # 1. Language detection
    lang = language or detect_language(question)
    log.info("RAG query started", language=lang)

    # 2. Search knowledge base via pgvector service
    # search_kb now handles embedding generation internally to keep RAM low
    raw_chunks = await search_kb(question, top_k=settings.TOP_K_RETRIEVAL)
    
    used_knowledge_base = len(raw_chunks) > 0

    if not raw_chunks:
        no_result_msg = (
            "Samahani, sikupata taarifa husika." if lang == "sw"
            else "Sorry, I could not find relevant information in the legal knowledge base."
        )
        return {
            "answer": no_result_msg,
            "language": lang,
            "retrieved_chunks": [],
            "clause_summaries": [],
            "risk_flags": [],
            "obligations": [],
            "used_knowledge_base": False,
            "disclaimer": "",
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    # 3. Build enriched chunk list
    retrieved_chunks = []
    context_parts = []

    for source, content, score in raw_chunks:
        retrieved_chunks.append({
            "text": content,
            "document_id": 0,
            "document_title": source,
            "chunk_index": 0,
            "relevance_score": score,
            "clause_number": None,
            "page_number": None
        })
        context_parts.append(f"[Source: {source}]\n{content}")

    context = "\n\n---\n\n".join(context_parts)

    # 4. Generate answer via Groq
    groq = get_groq_service()
    result = groq.ask(
        question=question,
        context=context,
        language=lang,
        history=conversation_history,
        used_knowledge_base=used_knowledge_base,
    )

    elapsed_ms = round((time.time() - start_time) * 1000, 2)
    
    # 5. Handle disclaimer split
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
        "disclaimer": disclaimer or "This is for informational purposes only.",
        "response_time_ms": elapsed_ms,
    }