"""AWS Lambda entry point for InferOps AI.

Mangum adapts the FastAPI ASGI app to API Gateway HTTP API v2 events.
lifespan="off" disables ASGI startup/shutdown, which Mangum cannot drive
in Lambda's stateless model.

Schema bootstrap (init_db) is intentionally NOT run here. Lambda enforces
a hard 10-second init-phase timeout, and a synchronous Supabase TLS
handshake + CREATE TABLE round-trip is enough on top of heavy module
imports to blow past it. The schema is seeded once via SQL pasted into
the Supabase SQL editor (see infra/terraform/README/section 11 of the
project README). Application code never recreates tables at runtime.
"""
from mangum import Mangum

from app.main import app


handler = Mangum(app, lifespan="off")
