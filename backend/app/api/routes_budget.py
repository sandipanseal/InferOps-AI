from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import RequestLog

router = APIRouter(prefix="/v1", tags=["budget"])


@router.get("/budget/usage")
async def get_budget_usage(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(
            RequestLog.selected_model.label("model"),
            func.count(RequestLog.id).label("requests"),
            func.coalesce(func.sum(RequestLog.estimated_cost_usd), 0).label(
                "estimated_cost"
            ),
        )
        .group_by(RequestLog.selected_model)
        .order_by(func.count(RequestLog.id).desc())
    )

    rows = (await db.execute(stmt)).all()

    return [
        {
            "model": row.model,
            "requests": int(row.requests or 0),
            "estimated_cost": float(row.estimated_cost or 0),
        }
        for row in rows
    ]