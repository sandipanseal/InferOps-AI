"""AWS Lambda entry point for InferOps AI.

Mangum adapts the FastAPI ASGI app to API Gateway HTTP API v2 events.
lifespan="off" disables ASGI startup/shutdown, which Mangum cannot drive
in Lambda's stateless model. We compensate by running init_db() once at
cold start, below.
"""
import asyncio
import logging
import os

from mangum import Mangum

from app.main import app

logger = logging.getLogger(__name__)


def _bootstrap_db() -> None:
    """Create SQLAlchemy tables on cold start. Idempotent — uses CREATE IF NOT EXISTS."""
    try:
        from app.db.init_db import init_db
        asyncio.run(init_db())
    except Exception as exc:
        logger.warning("init_db() skipped or failed on cold start: %s", exc)


if os.environ.get("INFEROPS_SKIP_INIT_DB") != "1":
    _bootstrap_db()


handler = Mangum(app, lifespan="off")
