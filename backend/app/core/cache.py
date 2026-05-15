import hashlib
import json
from app.core.redis_client import redis_client


def build_cache_key(prompt: str, priority: str, privacy: str) -> str:
    raw = f"{prompt}|{priority}|{privacy}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"cache:response:{digest}"


async def get_cached_response(prompt: str, priority: str, privacy: str):
    key = build_cache_key(prompt, priority, privacy)
    value = await redis_client.get(key)

    if not value:
        return None

    return json.loads(value)


async def set_cached_response(
    prompt: str,
    priority: str,
    privacy: str,
    data: dict,
    ttl_seconds: int = 3600,
):
    key = build_cache_key(prompt, priority, privacy)
    await redis_client.set(key, json.dumps(data), ex=ttl_seconds)