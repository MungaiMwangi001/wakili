"""Query model – stores user Q&A interactions for analytics."""
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Float, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Query(Base):
    __tablename__ = "queries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id"), nullable=True, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(5), default="en")
    retrieved_chunks: Mapped[dict] = mapped_column(JSON, nullable=True)
    response_time_ms: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
