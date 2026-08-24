import redis

from app.core.config import settings

_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


def set_redis_client(client: redis.Redis) -> None:
    global _redis_client
    _redis_client = client


def ping_redis() -> bool:
    try:
        return get_redis().ping()
    except redis.RedisError:
        return False


def redis_available() -> bool:
    return ping_redis()
