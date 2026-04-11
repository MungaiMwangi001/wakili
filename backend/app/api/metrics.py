"""
Metrics endpoint – GET /metrics/metrics
Returns analytics: document counts, query counts, response times.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.query import Query
from app.utils.auth_deps import get_current_user

router = APIRouter()


@router.get("/metrics")
async def get_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return usage statistics for the current user's dashboard."""
    doc_result = await db.execute(
        select(
            func.count(Document.id).label("total"),
            func.count(Document.id).filter(Document.status == "ready").label("ready"),
            func.count(Document.id).filter(Document.status == "processing").label("processing"),
            func.count(Document.id).filter(Document.status == "error").label("errors"),
        ).where(Document.user_id == current_user.id)
    )
    doc_stats = doc_result.one()

    query_result = await db.execute(
        select(
            func.count(Query.id).label("total_queries"),
            func.avg(Query.response_time_ms).label("avg_response_ms"),
        ).where(Query.user_id == current_user.id)
    )
    query_stats = query_result.one()

    lang_result = await db.execute(
        select(Query.language, func.count(Query.id).label("count"))
        .where(Query.user_id == current_user.id)
        .group_by(Query.language)
    )
    lang_breakdown = {row.language: row.count for row in lang_result}

    return {
        "documents": {
            "total": doc_stats.total or 0,
            "ready": doc_stats.ready or 0,
            "processing": doc_stats.processing or 0,
            "errors": doc_stats.errors or 0,
        },
        "queries": {
            "total": query_stats.total_queries or 0,
            "avg_response_ms": round(query_stats.avg_response_ms or 0, 2),
        },
        "language_breakdown": lang_breakdown,
    }
