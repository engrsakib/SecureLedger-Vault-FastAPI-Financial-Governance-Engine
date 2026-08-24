import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.rate_limit import enforce_rate_limit
from app.core.security import (
    create_token_pair,
    decode_access_token,
    decode_refresh_token,
    verify_password,
)
from app.core.token_store import get_session, revoke_session, rotate_session_tokens
from app.crud import user as user_crud
from app.database.session import get_db
from app.dependencies.auth import get_current_user, http_bearer
from app.models.user import User
from app.schemas.user import (
    MessageResponse,
    RefreshTokenRequest,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _build_token_response(session: dict) -> Token:
    return Token(
        access_token=session["access_token"],
        refresh_token=session["refresh_token"],
        token_type="bearer",
        session_id=session["session_id"],
        device_id=session["device_id"],
    )


def _issue_session_tokens(username: str, device_id: str) -> Token:
    session_id = str(uuid.uuid4())
    tokens = create_token_pair(session_id, device_id, username)
    rotate_session_tokens(
        username=username,
        device_id=device_id,
        session_id=session_id,
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        access_jti=tokens["access_jti"],
        refresh_jti=tokens["refresh_jti"],
    )
    return Token(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
        session_id=session_id,
        device_id=device_id,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new account. Password is hashed before storage.",
)
def register(
    request: Request,
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    enforce_rate_limit(request)
    if user_crud.get_user_by_username(db, username=user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    if user_crud.get_user_by_email(db, email=user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    return user_crud.create_user(db, user_in)


@router.post(
    "/login",
    response_model=Token,
    summary="Login and get JWT tokens",
    description="Authenticate with JSON body. Same device_id reuses the existing token session.",
)
def login(
    request: Request,
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    enforce_rate_limit(request)
    device_id = credentials.device_id or str(uuid.uuid4())

    user = user_crud.get_user_by_username(db, username=credentials.username)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    existing_session = get_session(user.username, device_id)
    if existing_session:
        return _build_token_response(existing_session)

    return _issue_session_tokens(user.username, device_id)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access and refresh token pair.",
)
def refresh_token(request: Request, body: RefreshTokenRequest):
    enforce_rate_limit(request)
    token_data = decode_refresh_token(body.refresh_token)

    if (
        token_data.username is None
        or token_data.device_id is None
        or token_data.jti is None
        or token_data.session_id is None
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    session = get_session(token_data.username, token_data.device_id)
    if not session or session["refresh_jti"] != token_data.jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked or is invalid",
        )

    tokens = create_token_pair(
        token_data.session_id, token_data.device_id, token_data.username
    )
    rotate_session_tokens(
        username=token_data.username,
        device_id=token_data.device_id,
        session_id=token_data.session_id,
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        access_jti=tokens["access_jti"],
        refresh_jti=tokens["refresh_jti"],
    )
    return Token(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
        session_id=token_data.session_id,
        device_id=token_data.device_id,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout and revoke session",
    description="Invalidate the current device session and revoke all tokens.",
)
def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    current_user: User = Depends(get_current_user),
):
    enforce_rate_limit(request)
    token_data = decode_access_token(credentials.credentials)
    if token_data.device_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    revoke_session(current_user.username, token_data.device_id)
    return MessageResponse(message="Logged out successfully")
