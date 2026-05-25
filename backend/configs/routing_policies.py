"""Routing policy constants.

These constants are evaluated at import time. To keep the same code path
working in both local Docker Compose (where a real local Ollama can run)
and in AWS Lambda (where it cannot), the *local* slot is swapped to
Ollama Cloud when ENVIRONMENT is a cloud environment.

Why a swap and not a separate branch in the router: the router itself is
already complex with safety / budget / complexity / priority cases. Doing
the substitution here keeps router.py environment-agnostic — it always
reaches for "LOCAL_MODEL" and the swap decides what physical destination
that maps to.
"""
import os

# Premium model never changes — it is the OpenAI escape hatch.
PREMIUM_MODEL = "gpt-4.1"
PREMIUM_PROVIDER = "openai"

CHEAP_MODEL = "mock-cheap"
CHEAP_PROVIDER = "mock"

BLOCKED_MODEL = "blocked"
BLOCKED_PROVIDER = "none"

LOW_COMPLEXITY_THRESHOLD = 0.55
HIGH_COMPLEXITY_THRESHOLD = 0.65
LOW_BUDGET_RATIO = 0.20

CACHE_MODEL = "redis-cache"
CACHE_PROVIDER = "cache"

# ── Local slot (cloud-aware) ─────────────────────────────────────────────────
# In Lambda we cannot reach a local Ollama, so the "local" destination
# becomes the next-cheapest privacy-preserving option: Ollama Cloud.
_CLOUD_ENVS = {"demo", "production", "staging", "aws-deploy"}
_IS_CLOUD = os.environ.get("ENVIRONMENT", "local") in _CLOUD_ENVS

if _IS_CLOUD:
    LOCAL_MODEL = os.environ.get("OLLAMA_CLOUD_MODEL", "gpt-oss:120b-cloud")
    LOCAL_PROVIDER = "ollama_cloud"
else:
    LOCAL_MODEL = "llama3.1:8b"
    LOCAL_PROVIDER = "ollama"


ROUTING_REASONS = {
    "blocked": "Request blocked by safety policy.",
    "local_privacy": (
        "Request routed to local model because {reason}."
        if not _IS_CLOUD
        else "Request routed to privacy-preserving cloud model because {reason}."
    ),
    "low_budget": "Daily budget is low; routed to cheapest available model.",
    "quality_premium": "High-complexity quality-optimized request routed to premium model.",
    "quality_local": (
        "Quality-optimized simple or medium request routed to local model instead of mock provider."
        if not _IS_CLOUD
        else "Quality-optimized simple or medium request routed to cost-effective cloud model."
    ),
    "latency_fast": "Latency-optimized request routed to fastest configured provider.",
    "cost_low": "Low-complexity task routed to cost-effective model.",
    "balanced_local": (
        "Medium-complexity task routed to local model to balance cost and quality."
        if not _IS_CLOUD
        else "Medium-complexity task routed to cost-effective cloud model to balance cost and quality."
    ),
}
