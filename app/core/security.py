import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.schemas.user import TokenData

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def _create_token(
    *,
    username: str,
    session_id: str,
    device_id: str,
    token_type: str,
    expires_delta: timedelta,
) -> tuple[str, str]:
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": username,
        "session_id": session_id,
        "device_id": device_id,
        "type": token_type,
        "jti": jti,
        "exp": expire,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jti


def create_token_pair(session_id: str, device_id: str, username: str) -> dict[str, str]:
    access_token, access_jti = _create_token(
        username=username,
        session_id=session_id,
        device_id=device_id,
        token_type=TOKEN_TYPE_ACCESS,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token, refresh_jti = _create_token(
        username=username,
        session_id=session_id,
        device_id=device_id,
        token_type=TOKEN_TYPE_REFRESH,
        expires_delta=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "access_jti": access_jti,
        "refresh_jti": refresh_jti,
        "session_id": session_id,
        "device_id": device_id,
    }


def decode_token(token: str, expected_type: str) -> TokenData:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str | None = payload.get("sub")
        session_id: str | None = payload.get("session_id")
        device_id: str | None = payload.get("device_id")
        token_type: str | None = payload.get("type")
        jti: str | None = payload.get("jti")

        if username is None or session_id is None or device_id is None or jti is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenData(
            username=username,
            session_id=session_id,
            device_id=device_id,
            jti=jti,
            token_type=token_type,
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def decode_access_token(token: str) -> TokenData:
    return decode_token(token, TOKEN_TYPE_ACCESS)


def decode_refresh_token(token: str) -> TokenData:
    return decode_token(token, TOKEN_TYPE_REFRESH)
