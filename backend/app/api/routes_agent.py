import time
import uuid
from typing import Any

import anyio
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.rag_agent import run_agent
from app.db.models import RequestLog
from app.db.session import get_db


router = APIRouter(prefix="/v1/agent", tags=["agent"])


class AgentRunRequest(BaseModel):
    question: str
    model: str | None = None


def _rag_chunk_count(steps: list[dict[str, Any]]) -> tuple[bool, int]:
    used = False
    chunks = 0
    for s in steps:
        if s.get("tool") == "rag_search":
            used = True
            obs = s.get("observation") or ""
            chunks += sum(
                1 for line in obs.splitlines() if line.strip().startswith("[")
            )
    return used, chunks


@router.post("/run")
async def agent_run(req: AgentRunRequest, db: AsyncSession = Depends(get_db)):
    start = time.perf_counter()
    result = await anyio.to_thread.run_sync(
        lambda: run_agent(question=req.question, model=req.model)
    )
    latency_ms = int((time.perf_counter() - start) * 1000)

    # Persist a RequestLog row so the run shows up in Logs / Dashboard / Budget.
    try:
        steps = result.get("steps") or []
        tools_used = result.get("tools_used") or []
        rag_used, rag_chunks = _rag_chunk_count(steps)

        agent_model = result.get("model") or "agent"
        # Prefer exact token usage from the LangChain callback; fall back to
        # a character-based estimate if the model didn't report usage_metadata.
        input_tokens = int(result.get("input_tokens") or 0)
        output_tokens = int(result.get("output_tokens") or 0)
        if input_tokens == 0:
            input_tokens = max(1, len(req.question) // 4)
        if output_tokens == 0:
            output_tokens = max(1, len(str(result.get("answer") or "")) // 4)

        # gpt-4o-mini list price ~ $0.15 / 1M input, $0.60 / 1M output.
        estimated_cost = round(
            (input_tokens * 0.15 + output_tokens * 0.60) / 1_000_000.0,
            6,
        )

        reason = (
            f"LangChain agent run ({agent_model}); "
            f"tools={', '.join(tools_used) if tools_used else 'none'}"
        )

        log = RequestLog(
            id=str(uuid.uuid4()),
            user_id="agent_user",
            input_preview=req.question[:300],
            response_preview=(str(result.get("answer") or ""))[:500],
            task_type="agent",
            priority="agent",
            privacy="normal",
            selected_model=agent_model,
            selected_provider="openai",
            routing_reason=reason,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=estimated_cost,
            contains_pii=False,
            prompt_injection_risk="low",
            blocked=False,
            fallback_used=False,
            fallback_reason=None,
            trace_id=str(uuid.uuid4()),
            rag_used=rag_used,
            rag_document=None,
            rag_filename=None,
            rag_chunks=rag_chunks,
            rag_top_score=None,
        )
        db.add(log)
        await db.commit()
    except Exception:
        await db.rollback()

    if isinstance(result, dict):
        result.setdefault("latency_ms", latency_ms)
    return result
