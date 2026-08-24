import json
from typing import Any

import redis

from app.core.config import settings
from app.core.redis_client import get_redis, redis_available

SESSION_KEY_PREFIX = "session"
ACTIVE_TOKEN_PREFIX = "active_token"


def _session_key(username: str, device_id: str) -> str:
    return f"{SESSION_KEY_PREFIX}:{username}:{device_id}"


def _active_token_key(username: str, device_id: str, jti: str) -> str:
    return f"{ACTIVE_TOKEN_PREFIX}:{username}:{device_id}:{jti}"


def get_session(username: str, device_id: str) -> dict[str, Any] | None:
    if not redis_available():
        return None
    try:
        raw = get_redis().get(_session_key(username, device_id))
        if not raw:
            return None
        return json.loads(raw)
    except redis.RedisError:
        return None


def save_session(
    username: str,
    device_id: str,
    session_id: str,
    access_token: str,
    refresh_token: str,
    access_jti: str,
    refresh_jti: str,
) -> None:
    if not redis_available():
        return
    try:
        redis_client = get_redis()
        session_data = {
            "username": username,
            "device_id": device_id,
            "session_id": session_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "access_jti": access_jti,
            "refresh_jti": refresh_jti,
        }
        ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60
        session_key = _session_key(username, device_id)
        redis_client.set(session_key, json.dumps(session_data), ex=ttl_seconds)
        redis_client.set(
            _active_token_key(username, device_id, access_jti),
            "1",
            ex=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        redis_client.set(
            _active_token_key(username, device_id, refresh_jti),
            "1",
            ex=ttl_seconds,
        )
    except redis.RedisError:
        return


def is_token_active(username: str, device_id: str, jti: str) -> bool:
    if not redis_available():
        return True
    try:
        return get_redis().exists(_active_token_key(username, device_id, jti)) == 1
    except redis.RedisError:
        return True


def revoke_session(username: str, device_id: str) -> None:
    if not redis_available():
        return
    try:
        session = get_session(username, device_id)
        if not session:
            return

        redis_client = get_redis()
        redis_client.delete(_session_key(username, device_id))
        redis_client.delete(
            _active_token_key(username, device_id, session["access_jti"])
        )
        redis_client.delete(
            _active_token_key(username, device_id, session["refresh_jti"])
        )
    except redis.RedisError:
        return


def rotate_session_tokens(
    username: str,
    device_id: str,
    session_id: str,
    access_token: str,
    refresh_token: str,
    access_jti: str,
    refresh_jti: str,
) -> None:
    revoke_session(username, device_id)
    save_session(
        username,
        device_id,
        session_id,
        access_token,
        refresh_token,
        access_jti,
        refresh_jti,
    )
