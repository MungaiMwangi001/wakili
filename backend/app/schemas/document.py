"""Pydantic schemas for document endpoints."""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class DocumentResponse(BaseModel):
    id: int
    title: str
    filename: str
    file_type: str
    file_size_bytes: int
    status: str
    clause_summaries: Optional[List[Dict[str, Any]]] = None
    risk_flags: Optional[List[Dict[str, Any]]] = None
    obligations: Optional[List[Dict[str, Any]]] = None
    chunk_count: int
    detected_language: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    message: str
    document_id: int
    status: str


# Alias so both names work — DocumentOut is used by the new documents.py
DocumentOut = DocumentResponse