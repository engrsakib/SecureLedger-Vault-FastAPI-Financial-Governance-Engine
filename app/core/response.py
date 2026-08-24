import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


def get_request_id(request: Request | None) -> str:
    if request is None:
        return str(uuid.uuid4())
    return getattr(request.state, "request_id", str(uuid.uuid4()))


def base_meta(request_id: str | None = None) -> dict[str, str]:
    return {
        "request_id": request_id or str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def success(
    *,
    data: Any = None,
    message: str = "Success",
    meta: Any = None,
    status_code: int = 200,
    next_step: Any = None,
    links: Any = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    return {
        "success": True,
        "status_code": status_code,
        "message": message,
        "data": data,
        "meta": meta,
        "next_step": next_step,
        "links": links,
        **base_meta(request_id),
    }


def error(
    *,
    message: str = "Something went wrong",
    status_code: int = 500,
    code: str | None = None,
    errors: Any = None,
    meta: Any = None,
    next_step: Any = None,
    links: Any = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    return {
        "success": False,
        "status_code": status_code,
        "message": message,
        "code": code,
        "errors": errors,
        "meta": meta,
        "next_step": next_step,
        "links": links,
        **base_meta(request_id),
    }


success_body = success
error_body = error


def _serialize_data(data: Any) -> Any:
    if data is None:
        return None
    if isinstance(data, BaseModel):
        return data.model_dump(mode="json")
    if isinstance(data, list):
        return [_serialize_data(item) for item in data]
    if isinstance(data, dict):
        return data
    if hasattr(data, "__dict__") and not isinstance(data, (str, int, float, bool)):
        return {
            key: value
            for key, value in data.__dict__.items()
            if not key.startswith("_")
        }
    return data


def success_result(
    request: Request | None = None,
    *,
    data: Any = None,
    message: str = "Success",
    status_code: int = 200,
    meta: Any = None,
    next_step: Any = None,
    links: Any = None,
) -> dict[str, Any]:
    """Return envelope dict for route handlers (Swagger `response_model` compatible)."""
    return success(
        data=_serialize_data(data),
        message=message,
        status_code=status_code,
        meta=meta,
        next_step=next_step,
        links=links,
        request_id=get_request_id(request),
    )


def success_response(
    request: Request | None = None,
    *,
    data: Any = None,
    message: str = "Success",
    status_code: int = 200,
    meta: Any = None,
    next_step: Any = None,
    links: Any = None,
) -> JSONResponse:
    body = success(
        data=_serialize_data(data),
        message=message,
        status_code=status_code,
        meta=meta,
        next_step=next_step,
        links=links,
        request_id=get_request_id(request),
    )
    return JSONResponse(status_code=status_code, content=body)


def error_response(
    request: Request | None = None,
    *,
    message: str = "Something went wrong",
    status_code: int = 500,
    code: str | None = None,
    errors: Any = None,
    meta: Any = None,
    next_step: Any = None,
    links: Any = None,
) -> JSONResponse:
    body = error(
        message=message,
        status_code=status_code,
        code=code,
        errors=errors,
        meta=meta,
        next_step=next_step,
        links=links,
        request_id=get_request_id(request),
    )
    return JSONResponse(status_code=status_code, content=body)
