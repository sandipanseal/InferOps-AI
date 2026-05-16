from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import RequestLog

router = APIRouter(prefix="/v1", tags=["logs"])


@router.get("/logs")
async def get_logs(limit: int = 100, db: AsyncSession = Depends(get_db)):
    stmt = select(RequestLog).order_by(desc(RequestLog.created_at)).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()

    return [
        {
            "id": row.id,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "user_id": row.user_id,
            "input_preview": row.input_preview,
            "response_preview": getattr(row, "response_preview", None),
            "task_type": row.task_type,
            "priority": row.priority,
            "privacy": row.privacy,
            "model": row.selected_model,
            "provider": row.selected_provider,
            "cost": row.estimated_cost_usd,
            "latency": row.latency_ms,
            "input_tokens": row.input_tokens,
            "output_tokens": row.output_tokens,
            "contains_pii": row.contains_pii,
            "injection_risk": row.prompt_injection_risk,
            "blocked": row.blocked,
            "fallback": row.fallback_used,
            "fallback_reason": row.fallback_reason,
            "routing_reason": row.routing_reason,
            "trace_id": row.trace_id,
            "rag_used": row.rag_used,
            "rag_document": row.rag_document,
            "rag_filename": row.rag_filename,
            "rag_chunks": row.rag_chunks,
            "rag_top_score": row.rag_top_score,
        }
        for row in rows
    ]