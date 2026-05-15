from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.db.models import RequestLog


async def get_daily_spend(db: AsyncSession, user_id: str) -> float:
    now = datetime.utcnow()
    start = datetime(now.year, now.month, now.day)
    stmt = select(func.coalesce(func.sum(RequestLog.estimated_cost_usd), 0.0)).where(
        RequestLog.user_id == user_id,
        RequestLog.created_at >= start,
    )
    result = await db.execute(stmt)
    return float(result.scalar_one())


async def get_budget_remaining(db: AsyncSession, user_id: str) -> tuple[float, float, float]:
    settings = get_settings()
    limit = settings.user_daily_budget_usd
    used = await get_daily_spend(db, user_id)
    remaining = max(0.0, limit - used)
    return used, limit, remaining
