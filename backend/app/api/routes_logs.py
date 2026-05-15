from fastapi import APIRouter, Depends
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models import RequestLog

router = APIRouter(prefix="/v1", tags=["logs"])


@router.get("/logs")
async def get_logs(limit: int = 100, db: AsyncSession = Depends(get_db)):
    """
    Returns recent request lifecycle logs for the Request Logs frontend page.
    """

    stmt = (
        select(RequestLog)
        .order_by(desc(RequestLog.created_at))
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()

    return [
        {
            "id": row.id,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "user_id": row.user_id,
            "model": row.selected_model,
            "provider": row.selected_provider,
            "cost_usd": row.estimated_cost_usd,
            "latency_ms": row.latency_ms,
            "contains_pii": row.contains_pii,
            "blocked": row.blocked,
            "fallback_used": row.fallback_used,
            "routing_reason": row.routing_reason,
            "response_preview": (
                row.response_preview[:300] if row.response_preview else None
            ),
            "rag_used": row.rag_used,
            "rag_document": row.rag_document,
            "rag_filename": row.rag_filename,
            "rag_chunks": row.rag_chunks,
            "rag_top_score": row.rag_top_score,
        }
        for row in rows
    ]
