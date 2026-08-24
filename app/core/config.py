import re

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_duration_minutes(value: str | int) -> int:
    if isinstance(value, int):
        return value
    raw = value.strip().lower()
    days_match = re.fullmatch(r"(\d+)\s*days?", raw)
    if days_match:
        return int(days_match.group(1)) * 24 * 60
    hours_match = re.fullmatch(r"(\d+)\s*hours?", raw)
    if hours_match:
        return int(hours_match.group(1)) * 60
    return int(raw)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 86400

    REDIS_URL: str = "redis://redis:6379/0"
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    @field_validator("REFRESH_TOKEN_EXPIRE_MINUTES", mode="before")
    @classmethod
    def parse_refresh_token_expire(cls, value: str | int) -> int:
        return parse_duration_minutes(value)


settings = Settings()
