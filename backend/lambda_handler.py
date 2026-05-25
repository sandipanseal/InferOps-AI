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


async def _bootstrap_async() -> None:
    """Create tables, then dispose the engine.

    Disposing matters because ``asyncio.run`` below creates a temporary
    event loop. The SQLAlchemy async engine binds its internal asyncpg
    connection pool to whichever loop opened those connections. Once
    ``asyncio.run`` tears its loop down, those pooled connections become
    invalid — and the next call (from Mangum's loop) raises
    "got Future <Future pending> attached to a different loop".

    Calling ``engine.dispose()`` closes the pool here so the engine
    lazily re-creates a fresh pool against Mangum's event loop on the
    first real request.
    """
    from app.db.init_db import init_db
    from app.db.session import engine

    await init_db()
    await engine.dispose()


def _bootstrap_db() -> None:
    try:
        asyncio.run(_bootstrap_async())
    except Exception as exc:
        logger.warning("init_db() skipped or failed on cold start: %s", exc)


if os.environ.get("INFEROPS_SKIP_INIT_DB") != "1":
    _bootstrap_db()


handler = Mangum(app, lifespan="off")
