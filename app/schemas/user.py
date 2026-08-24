from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    session_id: str
    device_id: str


class TokenData(BaseModel):
    username: str | None = None
    session_id: str | None = None
    device_id: str | None = None
    jti: str | None = None
    token_type: str | None = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class MessageResponse(BaseModel):
    message: str
