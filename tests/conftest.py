import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_MINUTES", "60Days")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("RATE_LIMIT_REQUESTS", "1000")
os.environ.setdefault("RATE_LIMIT_WINDOW_SECONDS", "60")

from collections.abc import Generator

import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.redis_client import set_redis_client
from app.database.base import Base
from app.database.session import SessionLocal, engine, get_db
from app.main import app

TEST_DEVICE_ID = "test-device-001"


@pytest.fixture(autouse=True)
def fake_redis():
    client = fakeredis.FakeRedis(decode_responses=True)
    set_redis_client(client)
    yield client
    client.flushall()


@pytest.fixture
def db() -> Generator[Session, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


from tests.helpers import get_success_data


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )
    response = client.post(
        "/auth/login",
        json={
            "username": "testuser",
            "password": "testpassword123",
            "device_id": TEST_DEVICE_ID,
        },
    )
    token = get_success_data(response)["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_transaction(client: TestClient, auth_headers: dict[str, str]) -> dict:
    response = client.post(
        "/transactions",
        json={
            "title": "Groceries",
            "amount": 150.0,
            "type": "expense",
            "category": "Food",
            "date": "2026-01-15",
        },
        headers=auth_headers,
    )
    return get_success_data(response)
