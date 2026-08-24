from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from app.core.rate_limit import enforce_rate_limit
from app.core.redis_client import ping_redis
from app.database.base import Base
from app.database.session import engine, wait_for_database
from app.models import transaction, user  # noqa: F401
from app.routers import auth, transactions
from app.schemas.root import DeveloperInfo, WelcomeResponse

PROJECT_NAME = "SecureLedger Vault"
API_VERSION = "1.2.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    wait_for_database()
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="SecureLedger Vault — Expense Tracker API",
    description=(
        "Personal Expense Tracker API with JWT authentication, Redis sessions, "
        "and rate limiting. All write endpoints accept **application/json**."
    ),
    version=API_VERSION,
    lifespan=lifespan,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": 2,
        "defaultModelExpandDepth": 2,
        "displayRequestDuration": True,
        "docExpansion": "list",
        "filter": True,
        "syntaxHighlight.theme": "monokai",
    },
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Paste the access_token from POST /auth/login",
        }
    }
    for path_item in openapi_schema["paths"].values():
        for operation in path_item.values():
            if isinstance(operation, dict) and operation.get("security") is None:
                if any(tag in operation.get("tags", []) for tag in ("Transactions",)):
                    operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

app.include_router(auth.router)
app.include_router(transactions.router)


@app.middleware("http")
async def global_rate_limit_middleware(request: Request, call_next):
    if request.url.path in {"/", "/health", "/docs", "/redoc", "/openapi.json"}:
        return await call_next(request)
    try:
        enforce_rate_limit(request)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return await call_next(request)


@app.get(
    "/",
    response_model=WelcomeResponse,
    tags=["Root"],
    summary="Welcome & API directory",
    description="Returns project welcome message, documentation links, system URLs, and developer info.",
)
def root(request: Request):
    base_url = str(request.base_url).rstrip("/")
    return WelcomeResponse(
        message=f"Welcome to {PROJECT_NAME} — Personal Expense Tracker API",
        project=PROJECT_NAME,
        version=API_VERSION,
        documentation={
            "swagger_ui": f"{base_url}/docs",
            "redoc": f"{base_url}/redoc",
            "openapi_json": f"{base_url}/openapi.json",
        },
        system={
            "root": f"{base_url}/",
            "health": f"{base_url}/health",
        },
        developer=DeveloperInfo(
            name="Md. Nazmus Sakib",
            username="engrsakib",
            website="https://engrsakib.com",
        ),
    )


@app.get("/health", tags=["Health"], summary="Health check")
def health_check():
    return {
        "status": "ok",
        "redis": "connected" if ping_redis() else "disconnected",
    }
