"""
Q&A endpoint – POST /ask
Runs the RAG pipeline with conversation memory and returns a structured legal answer.
"""
import time
import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.ask import AskRequest, AskResponse, RetrievedChunk
from app.services.pgvector_service import search_kb
from app.services.groq_service import get_groq_service

router = APIRouter()
log = structlog.get_logger()

@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest, db: AsyncSession = Depends(get_db)):
    start_time = time.time()
    log.info("Processing Q&A request", question=request.question)
    
    try:
        # 1. Search the Knowledge Base via pgvector
        # This function handles the lazy-loading of the SentenceTransformer model
        search_results = await search_kb(request.question, top_k=5)
        
        retrieved_chunks = []
        context_text = ""
        
        # 2. Map DB results (source, content, score) to RetrievedChunk schema
        for source, content, score in search_results:
            chunk = RetrievedChunk(
                text=content,
                document_id=0,  # KB items are global, not specific to an uploaded doc
                document_title=source,
                chunk_index=0,
                relevance_score=score,
                clause_number=None,
                page_number=None
            )
            retrieved_chunks.append(chunk)
            context_text += f"\nSource: {source}\nContent: {content}\n"

        # 3. Generate the Answer using Groq
        groq = get_groq_service()
        
        # Construct a simple prompt or use your existing RAG logic
        prompt = f"""
        You are Wakili, a Kenyan legal assistant. Use the following context to answer the user's question.
        If the context doesn't contain the answer, use your general knowledge of Kenyan law but add a disclaimer.
        
        Context:
        {context_text}
        
        User Question: {request.question}
        """
        
        # Assuming your groq_service has a method like this:
        answer = await groq.generate_answer(
            prompt=prompt,
            history=request.conversation_history
        )

        execution_time = (time.time() - start_time) * 1000  # Convert to ms

        return AskResponse(
            answer=answer,
            language=request.language or "en",
            retrieved_chunks=retrieved_chunks,
            used_knowledge_base=len(retrieved_chunks) > 0,
            disclaimer="This is for informational purposes only and not legal advice.",
            response_time_ms=execution_time
        )

    except Exception as e:
        log.error("Error in /ask endpoint", error=str(e))
        raise HTTPException(
            status_code=500, 
            detail="An error occurred while processing your legal query."
        )