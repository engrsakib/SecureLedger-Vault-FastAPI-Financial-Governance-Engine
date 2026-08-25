from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "engrsakib",
                "email": "info@engrsakib.com",
                "password": "1qazxsw2",
            }
        }
    )

    username: str = Field(..., description="Unique username for the account", examples=["engrsakib"])
    email: EmailStr = Field(..., description="Valid email address", examples=["info@engrsakib.com"])
    password: str = Field(..., description="Plain-text password (stored hashed)", examples=["1qazxsw2"])


class UserLogin(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "engrsakib",
                "password": "1qazxsw2",
                "device_id": "my-laptop-001",
            }
        }
    )

    username: str = Field(..., description="Registered username", examples=["engrsakib"])
    password: str = Field(..., description="Account password", examples=["1qazxsw2"])
    device_id: str | None = Field(
        default=None,
        description="Device identifier. Same device returns the same token session.",
        examples=["my-laptop-001"],
    )


class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "username": "engrsakib",
                "email": "info@engrsakib.com",
            }
        },
    )

    id: int = Field(..., description="Auto-generated user ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")


class Token(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "device_id": "my-laptop-001",
            }
        }
    )

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(..., description="Token type", examples=["bearer"])
    session_id: str = Field(..., description="Unique session ID for this device login")
    device_id: str = Field(..., description="Device ID tied to this session")


class TokenData(BaseModel):
    username: str | None = None
    session_id: str | None = None
    device_id: str | None = None
    jti: str | None = None
    token_type: str | None = None


class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            }
        }
    )

    refresh_token: str = Field(..., description="Valid refresh token from login response")


class MessageResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"message": "Operation completed successfully"}}
    )

    message: str = Field(..., description="Success or status message")
