"""Pydantic schemas for the Q&A (RAG) endpoint."""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ConversationMessage(BaseModel):
    role: str       # "user" or "assistant"
    content: str


class AskRequest(BaseModel):
    question: str
    document_id: Optional[int] = None
    language: Optional[str] = None
    conversation_history: List[ConversationMessage] = []


class RetrievedChunk(BaseModel):
    text: str
    document_id: int
    document_title: str
    chunk_index: int
    relevance_score: float
    clause_number: Optional[Any] = None
    page_number: Optional[int] = None


class AskResponse(BaseModel):
    answer: str
    language: str
    retrieved_chunks: List[RetrievedChunk]
    clause_summaries: Optional[List[Dict[str, Any]]] = None
    risk_flags: Optional[List[Dict[str, Any]]] = None
    obligations: Optional[List[Dict[str, Any]]] = None
    used_knowledge_base: bool = False
    disclaimer: str = ""
    response_time_ms: float