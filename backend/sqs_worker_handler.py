"""Lambda handler for the SQS worker function.

Drains the inferops-jobs SQS queue. Each message is a JSON envelope
{"job_type": "...", "payload": {...}} sent by app.core.job_queue.enqueue
from the API Lambda.

Supported job_types:
    log_request    — writes a RequestLog row to Postgres (raw psycopg2,
                     no SQLAlchemy/async to keep the worker lightweight).
    langfuse_trace — emits a trace to Langfuse.

Returns ``batchItemFailures`` so SQS retries only the messages that
actually failed instead of the whole batch.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    records: list[dict] = event.get("Records", [])
    failed: list[str] = []

    for record in records:
        message_id = record.get("messageId", "unknown")
        try:
            body = json.loads(record["body"])
            job_type = body["job_type"]
            payload = body["payload"]

            if job_type == "log_request":
                _handle_log_request(payload)
            elif job_type == "langfuse_trace":
                _handle_langfuse_trace(payload)
            else:
                logger.warning("Unknown job_type=%s id=%s", job_type, message_id)

        except Exception as exc:
            logger.exception("Failed to process message %s: %s", message_id, exc)
            failed.append(message_id)

    return {"batchItemFailures": [{"itemIdentifier": m} for m in failed]}


# Job handlers 


def _sync_dsn() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql://", 1)
    return url


def _handle_log_request(payload: dict[str, Any]) -> None:
    """Insert a row into request_logs.

    Uses raw psycopg2 with a column whitelist so unknown payload keys are
    silently dropped — keeps the API and worker loosely coupled.
    """
    import psycopg2

    columns = (
        "id",
        "created_at",
        "user_id",
        "input_preview",
        "response_preview",
        "task_type",
        "priority",
        "privacy",
        "selected_model",
        "selected_provider",
        "routing_reason",
        "latency_ms",
        "input_tokens",
        "output_tokens",
        "estimated_cost_usd",
        "contains_pii",
        "prompt_injection_risk",
        "blocked",
        "fallback_used",
        "fallback_reason",
        "trace_id",
        "rag_used",
        "rag_document",
        "rag_filename",
        "rag_chunks",
        "rag_top_score",
    )

    row = {col: payload.get(col) for col in columns if col in payload}
    if not row:
        return

    keys = list(row.keys())
    placeholders = ", ".join(["%s"] * len(keys))
    column_sql = ", ".join(keys)

    conn = psycopg2.connect(_sync_dsn())
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO request_logs ({column_sql}) VALUES ({placeholders}) "
                f"ON CONFLICT (id) DO NOTHING",
                [row[k] for k in keys],
            )
    finally:
        conn.close()


def _handle_langfuse_trace(payload: dict[str, Any]) -> None:
    from app.observability.langfuse_client import trace_request

    trace_request(**payload)
