from fastapi import HTTPException, Request, status

from app.core.config import settings
from app.core.redis_client import get_redis


def enforce_rate_limit(request: Request) -> None:
    client_host = request.client.host if request.client else "unknown"
    path = request.url.path
    key = f"rate_limit:{client_host}:{path}"

    redis_client = get_redis()
    count = redis_client.incr(key)
    if count == 1:
        redis_client.expire(key, settings.RATE_LIMIT_WINDOW_SECONDS)

    if count > settings.RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
        )
