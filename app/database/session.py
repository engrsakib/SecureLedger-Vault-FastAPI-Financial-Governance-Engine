import logging
import time
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

logger = logging.getLogger(__name__)

connect_args: dict = {}
pool_kwargs: dict = {"pool_pre_ping": True}

if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    if ":memory:" in settings.DATABASE_URL:
        pool_kwargs["poolclass"] = StaticPool
else:
    connect_args["connect_timeout"] = 10

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    **pool_kwargs,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def wait_for_database() -> None:
    if settings.DATABASE_URL.startswith("sqlite"):
        return

    last_error: Exception | None = None
    for attempt in range(1, settings.DB_CONNECT_RETRIES + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("Database connection established")
            return
        except OperationalError as exc:
            last_error = exc
            logger.warning(
                "Database connection attempt %s/%s failed: %s",
                attempt,
                settings.DB_CONNECT_RETRIES,
                exc,
            )
            if attempt < settings.DB_CONNECT_RETRIES:
                time.sleep(settings.DB_CONNECT_RETRY_DELAY_SECONDS)

    hint = (
        "If using Supabase inside Docker, use the IPv4 pooler URL from "
        "Project Settings -> Database -> Connection string (Transaction pooler), "
        "not the direct db.<project>.supabase.co host."
    )
    raise RuntimeError(f"Could not connect to the database. {hint}") from last_error


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
