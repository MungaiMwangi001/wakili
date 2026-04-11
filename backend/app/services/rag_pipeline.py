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
import time
import structlog

from app.services.embedding_service import EmbeddingService
from app.services.vector_store import (
    search_document,
    search_all_user_documents,
    search_knowledge_base,
)
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
    """
    Full RAG pipeline with conversation memory and knowledge base fallback.

    Args:
        question: User's natural language question
        document_ids: All user document IDs to search
        document_titles: Mapping of doc_id → title
        language: Override language detection ("en" | "sw" | None)
        document_id: Scope search to single document if provided
        conversation_history: Previous Q+A turns for follow-up support

    Returns:
        Dict with answer, language, retrieved_chunks, clause_summaries,
        risk_flags, obligations, used_knowledge_base, disclaimer,
        response_time_ms
    """
    start_time = time.time()

    # 1. Language detection
    lang = language or detect_language(question)
    log.info("RAG query started", language=lang, question_preview=question[:80])

    # 2. Embed the question (local, free)
    embedder = EmbeddingService.get_instance()
    query_embedding = embedder.embed_single(question)

    # 3. Retrieve from user documents
    if document_id:
        raw_chunks = search_document(
            document_id, query_embedding, top_k=settings.TOP_K_RETRIEVAL
        )
        for chunk in raw_chunks:
            chunk["document_id"] = document_id
    else:
        raw_chunks = search_all_user_documents(
            document_ids, query_embedding, top_k=settings.TOP_K_RETRIEVAL
        )

    # 4. Confidence check — best relevance score from user docs
    best_score = max((c["relevance_score"] for c in raw_chunks), default=0.0)
    used_knowledge_base = False

    if best_score < settings.CONFIDENCE_THRESHOLD:
        log.info(
            "Low confidence — trying knowledge base",
            best_score=best_score,
            threshold=settings.CONFIDENCE_THRESHOLD,
        )
        kb_chunks = search_knowledge_base(query_embedding, top_k=settings.TOP_K_RETRIEVAL)

        if kb_chunks:
            raw_chunks = kb_chunks
            used_knowledge_base = True
        elif not raw_chunks:
            # Neither user docs nor KB have anything useful
            no_result_msg = (
                "Samahani, sikupata taarifa husika katika hati zako au hifadhidata ya sheria. "
                "Tafadhali pakia hati inayohusiana au uliza upya."
                if lang == "sw"
                else "Sorry, I could not find relevant information in your documents or the "
                     "legal knowledge base. Please upload a relevant document or rephrase your question."
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

    # 5. Build enriched chunk list + context string
    # 5. Build enriched chunk list + context string
    retrieved_chunks = []
    context_parts = []

    for chunk in raw_chunks:
        doc_id = chunk.get("document_id", 0)
        # Pull metadata safely
        clause_num = chunk.get("metadata", {}).get("clause_number") or chunk.get("clause_number")
        page_num = chunk.get("metadata", {}).get("page_number")

        if used_knowledge_base:
            title = chunk.get("source", "Kenyan Law Knowledge Base")
        else:
            title = document_titles.get(doc_id, f"Document {doc_id}")

        # Add clause info to the retrieved_chunks list for the frontend
        retrieved_chunks.append({
            "text": chunk["text"],
            "document_id": doc_id,
            "document_title": title,
            "chunk_index": chunk["chunk_index"],
            "relevance_score": chunk["relevance_score"],
            "clause_number": clause_num, # NEW FIELD
            "page_number": page_num       # NEW FIELD
        })
        
        # Enrich the context with Clause info so Llama 3 can cite it accurately
        source_label = f"Source: {title}"
        if clause_num:
            source_label += f" | Clause: {clause_num}"
            
        context_parts.append(f"[{source_label}]\n{chunk['text']}")

    context = "\n\n---\n\n".join(context_parts)

    

    # 6. Generate answer via Groq (with conversation history)
    groq = get_groq_service()
    result = groq.ask(
        question=question,
        context=context,
        language=lang,
        history=conversation_history,
        used_knowledge_base=used_knowledge_base,
    )

    elapsed_ms = round((time.time() - start_time) * 1000, 2)
    log.info(
        "RAG query completed",
        response_time_ms=elapsed_ms,
        used_knowledge_base=used_knowledge_base,
        best_score=best_score,
    )

    # Split disclaimer out of answer for frontend to render separately
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
        "disclaimer": disclaimer,
        "response_time_ms": elapsed_ms,
    }


async def process_document_analysis(document_id: int, full_text: str, lang: str) -> dict:
    """
    Run document analysis after upload.
    Sends first ~3000 chars to Groq to extract clause summaries,
    risk flags, and obligations for storage in the Document record.
    """
    log.info("Document analysis started", document_id=document_id, language=lang)
    groq = get_groq_service()
    result = groq.analyse(full_text, lang)
    log.info("Document analysis complete", document_id=document_id)
    return {
        "clause_summaries": result.get("clause_summaries", []),
        "risk_flags": result.get("risk_flags", []),
        "obligations": result.get("obligations", []),
    }
