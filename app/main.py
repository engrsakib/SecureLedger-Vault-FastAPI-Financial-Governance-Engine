from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.rate_limit import enforce_rate_limit
from app.core.redis_client import ping_redis
from app.database.base import Base
from app.database.session import engine, wait_for_database
from app.models import transaction, user  # noqa: F401
from app.routers import auth, transactions


@asynccontextmanager
async def lifespan(app: FastAPI):
    wait_for_database()
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Personal Expense Tracker API",
    description="Track income and expenses with JWT authentication, Redis sessions, and rate limiting",
    version="1.1.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(transactions.router)


@app.middleware("http")
async def global_rate_limit_middleware(request: Request, call_next):
    if request.url.path not in {"/health", "/docs", "/redoc", "/openapi.json"}:
        try:
            enforce_rate_limit(request)
        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code, content={"detail": exc.detail}
            )
    return await call_next(request)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "redis": "connected" if ping_redis() else "disconnected",
    }
