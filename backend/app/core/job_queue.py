"""SQS-backed async job queue.

In cloud, heavy side-effects (Postgres request log writes, Langfuse
uploads) are offloaded to a separate worker Lambda so the API Lambda can
return to the user as soon as the LLM responds.

In local dev SQS_QUEUE_URL is empty — `enqueue` becomes a fire-and-forget
async hand-off to a background thread so behaviour matches: the request
returns immediately and the write happens on its own.
"""
from __future__ import annotations

import json
import logging
import os
import threading
from typing import Any

logger = logging.getLogger(__name__)

SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL", "")
AWS_REGION_NAME = (
    os.environ.get("AWS_REGION_NAME")
    or os.environ.get("AWS_REGION")
    or "eu-central-1"
)

_sqs_client = None


def _get_sqs():
    global _sqs_client
    if _sqs_client is None:
        import boto3  # type: ignore

        _sqs_client = boto3.client("sqs", region_name=AWS_REGION_NAME)
    return _sqs_client


def enqueue(job_type: str, payload: dict[str, Any]) -> bool:
    """Enqueue a job. Falls back to local execution if SQS is not configured."""
    if not SQS_QUEUE_URL:
        threading.Thread(
            target=_execute_locally,
            args=(job_type, payload),
            daemon=True,
        ).start()
        return True

    try:
        sqs = _get_sqs()
        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps({"job_type": job_type, "payload": payload}),
        )
        return True
    except Exception as exc:
        logger.warning("SQS enqueue failed for job_type=%s: %s", job_type, exc)
        threading.Thread(
            target=_execute_locally,
            args=(job_type, payload),
            daemon=True,
        ).start()
        return False


def _execute_locally(job_type: str, payload: dict[str, Any]) -> None:
    """Local fallback for when SQS is not configured."""
    try:
        if job_type == "langfuse_trace":
            from app.observability.langfuse_client import trace_request

            trace_request(**payload)
        else:
            logger.debug("No local handler for job_type=%s", job_type)
    except Exception as exc:
        logger.warning("Local job execution failed for %s: %s", job_type, exc)


def enqueue_langfuse_trace(trace_data: dict[str, Any]) -> bool:
    return enqueue("langfuse_trace", trace_data)


def enqueue_request_log(log_data: dict[str, Any]) -> bool:
    """Reserved for offloaded request log writes when async writes via the
    primary SQLAlchemy session aren't desired."""
    return enqueue("log_request", log_data)
