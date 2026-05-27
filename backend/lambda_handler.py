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
# IMPORTANT: These env overrides MUST happen before any other import.
#
# Lambda forces HOME=/home/sbx_user<N> which is a read-only filesystem.
# huggingface_hub / sentence-transformers / transformers all write lock
# files, telemetry, and stale-cache metadata under $HOME/.cache/huggingface
# by default. Anything that hits expanduser("~") explodes with
# `OSError: [Errno 30] Read-only file system`.
#
# Re-pointing HOME at /tmp (Lambda's only writable directory, 512MB-10GB)
# absorbs every accidental write without affecting reads of the baked
# model under /var/task/hf_cache.
#
# HF_HUB_OFFLINE / TRANSFORMERS_OFFLINE belt-and-suspenders: even if the
# Docker ENVs get stripped, this guarantees no network call to HF Hub at
# runtime (where it would just fail and write a lock file anyway).
import os

_HF_CACHE_ROOT = "/var/task/hf_cache"

os.environ["HOME"] = "/tmp"  # NOSONAR — Lambda's only writable directory
os.environ.setdefault("HF_HOME", _HF_CACHE_ROOT)
os.environ.setdefault("HF_HUB_CACHE", f"{_HF_CACHE_ROOT}/hub")
os.environ.setdefault("TRANSFORMERS_CACHE", _HF_CACHE_ROOT)
os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", _HF_CACHE_ROOT)
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/.cache")  # NOSONAR

from mangum import Mangum  # noqa: E402

from app.main import app  # noqa: E402


handler = Mangum(app, lifespan="off")
