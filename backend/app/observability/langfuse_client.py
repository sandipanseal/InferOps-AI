"""Langfuse client.

Cloud observability for the aws-deploy stack. Degrades silently if the
public/secret keys are not set (i.e. local Docker Compose runs), so adding
Langfuse calls inside the request path never breaks local dev or tests.
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_client = None
_initialized = False


def _get_client():
    """Initialize and cache the Langfuse client once per container."""
    global _client, _initialized
    if _initialized:
        return _client

    _initialized = True

    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "")

    if not public_key or not secret_key:
        return None

    try:
        from langfuse import Langfuse  # type: ignore

        _client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
    except Exception as exc:
        logger.warning("Langfuse init failed (continuing without it): %s", exc)
        _client = None

    return _client


def trace_request(
    request_id: str,
    user_id: str,
    selected_model: str,
    selected_provider: str,
    routing_reason: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
    estimated_cost_usd: float,
    safety: dict[str, Any] | None = None,
    rag_used: bool = False,
    cache_hit: bool = False,
    agent_run: bool = False,
) -> None:
    """Emit a routing-level trace + LLM generation span.

    Never raises — observability failures must not bring down the request.
    """
    client = _get_client()
    if client is None:
        return

    safety = safety or {}

    try:
        trace = client.trace(
            id=request_id,
            name="inferops-chat",
            user_id=user_id,
            tags=["inferops", selected_provider, selected_model],
            metadata={
                "routing_reason": routing_reason,
                "rag_used": rag_used,
                "cache_hit": cache_hit,
                "agent_run": agent_run,
                "safety_blocked": safety.get("blocked", False),
                "contains_pii": safety.get("contains_pii", False),
                "prompt_injection_risk": safety.get("prompt_injection_risk"),
            },
        )
        trace.generation(
            name="llm-generation",
            model=selected_model,
            usage={
                "input": input_tokens,
                "output": output_tokens,
                "unit": "TOKENS",
            },
            metadata={
                "latency_ms": latency_ms,
                "estimated_cost_usd": estimated_cost_usd,
                "provider": selected_provider,
            },
        )
        client.flush()
    except Exception as exc:
        logger.debug("Langfuse trace_request swallowed: %s", exc)


def trace_eval_score(
    request_id: str,
    score_name: str,
    score_value: float,
    comment: str | None = None,
) -> None:
    """Attach an eval score (RAGAS, judge) to an existing trace."""
    client = _get_client()
    if client is None:
        return

    try:
        client.score(
            trace_id=request_id,
            name=score_name,
            value=score_value,
            comment=comment,
        )
        client.flush()
    except Exception as exc:
        logger.debug("Langfuse trace_eval_score swallowed: %s", exc)
