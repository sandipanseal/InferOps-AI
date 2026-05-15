from app.core.redis_client import redis_client


class RateLimitExceeded(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


async def check_daily_user_limit(user_id: str, limit: int = 100):
    key = f"rate:user:{user_id}:daily"

    current = await redis_client.incr(key)

    if current == 1:
        await redis_client.expire(key, 60 * 60 * 24)

    if current > limit:
        raise RateLimitExceeded(f"Daily user request limit exceeded: {limit}")

    return {
        "limit": limit,
        "used": current,
        "remaining": max(0, limit - current),
    }


async def check_premium_hourly_limit(user_id: str, limit: int = 10):
    key = f"rate:user:{user_id}:premium_hourly"

    current = await redis_client.incr(key)

    if current == 1:
        await redis_client.expire(key, 60 * 60)

    if current > limit:
        raise RateLimitExceeded(f"Premium hourly limit exceeded: {limit}")

    return {
        "limit": limit,
        "used": current,
        "remaining": max(0, limit - current),
    }