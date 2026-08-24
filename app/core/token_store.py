import json
from typing import Any

from app.core.config import settings
from app.core.redis_client import get_redis

SESSION_KEY_PREFIX = "session"
ACTIVE_TOKEN_PREFIX = "active_token"


def _session_key(username: str, device_id: str) -> str:
    return f"{SESSION_KEY_PREFIX}:{username}:{device_id}"


def _active_token_key(username: str, device_id: str, jti: str) -> str:
    return f"{ACTIVE_TOKEN_PREFIX}:{username}:{device_id}:{jti}"


def get_session(username: str, device_id: str) -> dict[str, Any] | None:
    raw = get_redis().get(_session_key(username, device_id))
    if not raw:
        return None
    return json.loads(raw)


def save_session(
    username: str,
    device_id: str,
    session_id: str,
    access_token: str,
    refresh_token: str,
    access_jti: str,
    refresh_jti: str,
) -> None:
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


def is_token_active(username: str, device_id: str, jti: str) -> bool:
    return get_redis().exists(_active_token_key(username, device_id, jti)) == 1


def revoke_session(username: str, device_id: str) -> None:
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
