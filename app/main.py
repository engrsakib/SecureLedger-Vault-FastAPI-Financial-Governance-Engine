from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.core.config import settings
from app.core.handlers import register_exception_handlers
from app.core.openapi_responses import (
    AUTH_ERRORS,
    PROTECTED_ERRORS,
    PUBLIC_ERRORS,
    error_responses,
    merge_openapi_error_responses,
)
from app.core.rate_limit import enforce_rate_limit
from app.core.redis_client import ping_redis
from app.core.response import error_response, success_result
from app.core.url import get_public_base_url
import app.models.transaction
import app.models.user
from app.database.base import Base
from app.database.session import engine, wait_for_database
from app.middleware.request_context import RequestContextMiddleware
from app.routers import auth, transactions
from app.schemas.envelope import ApiSuccessResponse
from app.schemas.root import DeveloperInfo, HealthData, WelcomeData

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
        "and rate limiting.\n\n"
        "## Response format\n\n"
        "Every endpoint returns a **unified JSON envelope**:\n\n"
        "**Success** — `success`, `status_code`, `message`, `data`, `meta`, "
        "`next_step`, `links`, `request_id`, `timestamp`\n\n"
        "**Error** — same fields plus `code` and `errors` (`success: false`)\n\n"
        "Login tokens are in `data.access_token`. Use **Authorize** with "
        "`Bearer <access_token>` for protected routes."
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
            "description": (
                "Required for protected routes. "
                "1) POST /auth/login to get access_token from data.access_token. "
                "2) Click Authorize and paste: Bearer <access_token>"
            ),
        }
    }
    openapi_schema["servers"] = [
        {"url": "/", "description": "Current host (recommended for Swagger)"},
    ]
    if settings.PUBLIC_BASE_URL:
        openapi_schema["servers"].append(
            {
                "url": settings.PUBLIC_BASE_URL.rstrip("/"),
                "description": "Production server",
            }
        )
    protected_paths = ("/transactions",)
    for path, path_item in openapi_schema["paths"].items():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "delete", "patch"}:
                continue
            if not isinstance(operation, dict):
                continue
            if path.startswith(protected_paths) or path.endswith("/logout"):
                operation["security"] = [{"BearerAuth": []}]
                merge_openapi_error_responses(operation.setdefault("responses", {}), PROTECTED_ERRORS)
            elif path.startswith("/auth"):
                merge_openapi_error_responses(operation.setdefault("responses", {}), AUTH_ERRORS)
            else:
                merge_openapi_error_responses(operation.setdefault("responses", {}), PUBLIC_ERRORS)

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
register_exception_handlers(app)

app.add_middleware(RequestContextMiddleware)
app.include_router(auth.router)
app.include_router(transactions.router)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.middleware("http")
async def global_rate_limit_middleware(request: Request, call_next):
    if request.url.path in {"/", "/health", "/docs", "/redoc", "/openapi.json"}:
        return await call_next(request)
    try:
        enforce_rate_limit(request)
    except HTTPException as exc:
        return error_response(
            request,
            message=str(exc.detail),
            status_code=exc.status_code,
            code="RATE_LIMIT_EXCEEDED" if exc.status_code == 429 else None,
        )
    except Exception:
        return error_response(
            request,
            message="Service temporarily unavailable",
            status_code=503,
            code="SERVICE_UNAVAILABLE",
        )
    return await call_next(request)


@app.get(
    "/",
    tags=["Root"],
    summary="Welcome & API directory",
    response_model=ApiSuccessResponse[WelcomeData],
    responses=error_responses(*PUBLIC_ERRORS),
)
def root(request: Request):
    base_url = get_public_base_url(request)
    return success_result(
        request,
        data=WelcomeData(
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
        ),
        message=f"Welcome to {PROJECT_NAME} — Personal Expense Tracker API",
        links={
            "docs": f"{base_url}/docs",
            "health": f"{base_url}/health",
            "login": f"{base_url}/auth/login",
            "register": f"{base_url}/auth/register",
        },
        next_step={"action": "register", "url": f"{base_url}/auth/register"},
    )


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    response_model=ApiSuccessResponse[HealthData],
    responses=error_responses(*PUBLIC_ERRORS),
)
def health_check(request: Request):
    return success_result(
        request,
        data=HealthData(
            status="ok",
            redis="connected" if ping_redis() else "disconnected",
        ),
        message="Service is healthy",
    )
