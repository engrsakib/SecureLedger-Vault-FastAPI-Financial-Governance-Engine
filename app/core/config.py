import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_duration_minutes(value: str | int | None) -> int:
    if value is None:
        return 86400
    if isinstance(value, int):
        return value
    raw = str(value).strip()
    if not raw:
        return 86400
    lowered = raw.lower()
    days_match = re.fullmatch(r"(\d+)\s*days?", lowered)
    if days_match:
        return int(days_match.group(1)) * 24 * 60
    hours_match = re.fullmatch(r"(\d+)\s*hours?", lowered)
    if hours_match:
        return int(hours_match.group(1)) * 60
    return int(raw)


def normalize_database_url(url: str) -> str:
    normalized = url.strip()
    if normalized.startswith("postgres://"):
        normalized = "postgresql://" + normalized[len("postgres://") :]

    parsed = urlparse(normalized)
    if parsed.scheme not in {"postgresql", "sqlite"}:
        return normalized

    if parsed.scheme == "sqlite":
        return normalized

    query = parse_qs(parsed.query)
    if "sslmode" not in query:
        query["sslmode"] = ["require"]
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))


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
    DB_CONNECT_RETRIES: int = 5
    DB_CONNECT_RETRY_DELAY_SECONDS: int = 3
    PUBLIC_BASE_URL: str = ""
    CORS_ALLOW_ORIGINS: str = ""

    @property
    def cors_origins(self) -> list[str]:
        origins: list[str] = []
        if self.CORS_ALLOW_ORIGINS.strip():
            origins.extend(
                origin.strip()
                for origin in self.CORS_ALLOW_ORIGINS.split(",")
                if origin.strip()
            )
        if self.PUBLIC_BASE_URL.strip():
            public_origin = self.PUBLIC_BASE_URL.rstrip("/")
            if public_origin not in origins:
                origins.append(public_origin)
        return origins

    @field_validator("REFRESH_TOKEN_EXPIRE_MINUTES", mode="before")
    @classmethod
    def parse_refresh_token_expire(cls, value: str | int | None) -> int:
        return parse_duration_minutes(value)

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_db_url(cls, value: str) -> str:
        return normalize_database_url(value)


settings = Settings()
