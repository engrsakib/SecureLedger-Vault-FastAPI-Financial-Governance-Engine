from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.response import error_response


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        detail = exc.detail
        errors = None
        code = None
        if isinstance(detail, dict):
            message = detail.get("message", "Request failed")
            errors = detail.get("errors")
            code = detail.get("code")
        elif isinstance(detail, list):
            message = "Validation failed"
            errors = detail
            code = "VALIDATION_ERROR"
        else:
            message = str(detail)

        response = error_response(
            request,
            message=message,
            status_code=exc.status_code,
            code=code,
            errors=errors,
        )
        if exc.headers:
            for key, value in exc.headers.items():
                response.headers[key] = value
        return response

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ):
        return error_response(
            request,
            message=str(exc.detail),
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        return error_response(
            request,
            message="Validation error",
            status_code=422,
            code="VALIDATION_ERROR",
            errors=exc.errors(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return error_response(
            request,
            message="Something went wrong",
            status_code=500,
            code="INTERNAL_SERVER_ERROR",
        )
