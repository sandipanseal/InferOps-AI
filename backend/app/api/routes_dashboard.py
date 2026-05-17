from fastapi import APIRouter, Depends
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models import RequestLog
from app.db.models import Conversation, ConversationMessage
from app.evals.eval_runner import run_eval_suite
from app.observability.metrics import (
    EVAL_RUNS_TOTAL,
    EVAL_CASES_TOTAL,
    EVAL_ROUTING_ACCURACY,
)

router = APIRouter(prefix="/v1", tags=["dashboard"])


@router.get("/dashboard/summary")
async def dashboard_summary(db: AsyncSession = Depends(get_db)):
    total_stmt = select(
        func.count(RequestLog.id),
        func.coalesce(func.sum(RequestLog.estimated_cost_usd), 0.0),
        func.coalesce(func.avg(RequestLog.latency_ms), 0.0),
    )

    total = (await db.execute(total_stmt)).one()

    fallback_stmt = select(func.count(RequestLog.id)).where(RequestLog.fallback_used == True)
    fallback_count = (await db.execute(fallback_stmt)).scalar_one()

    safety_stmt = select(func.count(RequestLog.id)).where(RequestLog.blocked == True)
    blocked_count = (await db.execute(safety_stmt)).scalar_one()

    pii_stmt = select(func.count(RequestLog.id)).where(RequestLog.contains_pii == True)
    pii_count = (await db.execute(pii_stmt)).scalar_one()

    latency_rows_stmt = select(RequestLog.latency_ms).order_by(RequestLog.latency_ms)
    latency_rows = (await db.execute(latency_rows_stmt)).scalars().all()

    p95_latency = 0
    if latency_rows:
        index = int(0.95 * (len(latency_rows) - 1))
        p95_latency = latency_rows[index]

    model_stmt = (
        select(
            RequestLog.selected_model,
            func.count(RequestLog.id),
            func.coalesce(func.sum(RequestLog.estimated_cost_usd), 0.0),
            func.coalesce(func.avg(RequestLog.latency_ms), 0.0),
        )
        .group_by(RequestLog.selected_model)
        .order_by(func.count(RequestLog.id).desc())
    )

    model_rows = (await db.execute(model_stmt)).all()

    recent_stmt = (
        select(RequestLog)
        .order_by(desc(RequestLog.created_at))
        .limit(8)
    )

    recent_rows = (await db.execute(recent_stmt)).scalars().all()

    # Simple estimate: assume every non-premium request would have cost $0.002 if sent to premium model.
    non_premium_stmt = (
        select(func.count(RequestLog.id))
        .where(RequestLog.selected_model.notin_(["gpt-4.1", "blocked"]))
    )
    non_premium_count = (await db.execute(non_premium_stmt)).scalar_one()
    estimated_cost_saved = round(non_premium_count * 0.002, 6)

    return {
        "total_requests": total[0],
        "total_cost_usd": round(float(total[1]), 6),
        "avg_latency_ms": round(float(total[2]), 2),
        "p95_latency_ms": p95_latency,
        "fallback_count": fallback_count,
        "safety_blocks": blocked_count,
        "pii_detections": pii_count,
        "active_models": len(model_rows),
        "estimated_cost_saved_usd": estimated_cost_saved,
        "model_distribution": [
            {
                "model": r[0],
                "requests": r[1],
                "cost_usd": round(float(r[2]), 6),
                "avg_latency_ms": round(float(r[3]), 2),
            }
            for r in model_rows
        ],
        "recent_requests": [
            {
                "id": r.id,
                "created_at": r.created_at.isoformat(),
                "model": r.selected_model,
                "provider": r.selected_provider,
                "cost_usd": r.estimated_cost_usd,
                "latency_ms": r.latency_ms,
                "contains_pii": r.contains_pii,
                "blocked": r.blocked,
                "fallback_used": r.fallback_used,
                "routing_reason": r.routing_reason,
            }
            for r in recent_rows
        ],
    }

@router.get("/requests")
async def list_requests(limit: int = 50, db: AsyncSession = Depends(get_db)):
    stmt = select(RequestLog).order_by(desc(RequestLog.created_at)).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "input_preview": r.input_preview,
            "selected_model": r.selected_model,
            "selected_provider": r.selected_provider,
            "routing_reason": r.routing_reason,
            "latency_ms": r.latency_ms,
            "estimated_cost_usd": r.estimated_cost_usd,
            "contains_pii": r.contains_pii,
            "prompt_injection_risk": r.prompt_injection_risk,
            "blocked": r.blocked,
            "fallback_used": r.fallback_used,
            "trace_id": r.trace_id,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]

@router.get("/usage")
async def usage(db: AsyncSession = Depends(get_db)):
    stmt = select(RequestLog.selected_model, func.coalesce(func.sum(RequestLog.estimated_cost_usd), 0.0), func.count(RequestLog.id)).group_by(RequestLog.selected_model)
    rows = (await db.execute(stmt)).all()
    return [{"model": r[0], "cost_usd": round(float(r[1]), 6), "requests": r[2]} for r in rows]

@router.get("/conversations")
async def list_conversations(user_id: str = "demo_user", db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(desc(Conversation.created_at))
        .limit(50)
    )
    rows = (await db.execute(stmt)).scalars().all()

    return [
        {
            "id": r.id,
            "title": r.title,
            "user_id": r.user_id,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at)
    )
    rows = (await db.execute(stmt)).scalars().all()

    return [
        {
            "id": r.id,
            "conversation_id": r.conversation_id,
            "role": r.role,
            "content": r.content,
            "model": r.model,
            "provider": r.provider,
            "request_id": r.request_id,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]

@router.get("/requests/{request_id}")
async def get_request_detail(request_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(RequestLog).where(RequestLog.id == request_id)
    row = (await db.execute(stmt)).scalar_one_or_none()

    if row is None:
        return {"error": "request_not_found"}

    response_stmt = (
        select(ConversationMessage)
        .where(
            ConversationMessage.request_id == request_id,
            ConversationMessage.role == "assistant",
        )
        .order_by(ConversationMessage.created_at.desc())
        .limit(1)
    )

    response_row = (await db.execute(response_stmt)).scalar_one_or_none()

    assistant_response = response_row.content if response_row else None

    return {
        "id": row.id,
        "user_id": row.user_id,
        "input_preview": row.input_preview,
        "assistant_response": assistant_response,
        "assistant_response_preview": assistant_response[:800] if assistant_response else None,
        "task_type": row.task_type,
        "priority": row.priority,
        "privacy": row.privacy,
        "selected_model": row.selected_model,
        "selected_provider": row.selected_provider,
        "routing_reason": row.routing_reason,
        "latency_ms": row.latency_ms,
        "input_tokens": row.input_tokens,
        "output_tokens": row.output_tokens,
        "estimated_cost_usd": row.estimated_cost_usd,
        "contains_pii": row.contains_pii,
        "prompt_injection_risk": row.prompt_injection_risk,
        "blocked": row.blocked,
        "fallback_used": row.fallback_used,
        "fallback_reason": row.fallback_reason,
        "trace_id": row.trace_id,
        "created_at": row.created_at.isoformat(),
    }


@router.get("/safety/events")
async def safety_events(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(RequestLog)
        .where(
            (RequestLog.contains_pii == True)
            | (RequestLog.blocked == True)
            | (RequestLog.prompt_injection_risk.in_(["medium", "high"]))
        )
        .order_by(desc(RequestLog.created_at))
        .limit(100)
    )

    rows = (await db.execute(stmt)).scalars().all()

    total_pii = (
        await db.execute(
            select(func.count(RequestLog.id)).where(RequestLog.contains_pii == True)
        )
    ).scalar_one()

    total_blocked = (
        await db.execute(
            select(func.count(RequestLog.id)).where(RequestLog.blocked == True)
        )
    ).scalar_one()

    total_high_risk = (
        await db.execute(
            select(func.count(RequestLog.id)).where(
                RequestLog.prompt_injection_risk == "high"
            )
        )
    ).scalar_one()

    total_medium_risk = (
        await db.execute(
            select(func.count(RequestLog.id)).where(
                RequestLog.prompt_injection_risk == "medium"
            )
        )
    ).scalar_one()

    return {
        "summary": {
            "pii_detections": total_pii,
            "blocked_requests": total_blocked,
            "high_risk_injection_attempts": total_high_risk,
            "medium_risk_injection_attempts": total_medium_risk,
        },
        "events": [
            {
                "id": r.id,
                "created_at": r.created_at.isoformat(),
                "input_preview": r.input_preview,
                "model": r.selected_model,
                "provider": r.selected_provider,
                "contains_pii": r.contains_pii,
                "prompt_injection_risk": r.prompt_injection_risk,
                "blocked": r.blocked,
                "routing_reason": r.routing_reason,
                "trace_id": r.trace_id,
            }
            for r in rows
        ],
    }


@router.get("/evals/summary")
async def evals_summary():
    return {
        "routing_accuracy": 0.0,
        "pii_detection_accuracy": 0.0,
        "prompt_injection_block_accuracy": 0.0,
        "last_run": None,
        "message": "Run the evaluation suite to generate metrics.",
    }


@router.post("/evals/run")
async def run_evals():
    result = run_eval_suite()
    try:
        EVAL_RUNS_TOTAL.inc()
        passed = int(result.get("passed_cases", 0))
        total = int(result.get("total_cases", 0))
        failed = max(total - passed, 0)
        if passed:
            EVAL_CASES_TOTAL.labels(result="passed").inc(passed)
        if failed:
            EVAL_CASES_TOTAL.labels(result="failed").inc(failed)
        acc = result.get("routing_accuracy")
        if acc is not None:
            # eval_runner returns 0..1; expose as 0..100 percent
            EVAL_ROUTING_ACCURACY.set(float(acc) * 100.0 if float(acc) <= 1.0 else float(acc))
    except Exception:
        pass
    return result