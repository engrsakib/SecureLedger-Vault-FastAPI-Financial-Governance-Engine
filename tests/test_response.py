import json
import uuid

import pytest
from pydantic import BaseModel
from starlette.requests import Request

from app.core.response import (
    ERROR_FIELD_ORDER,
    SUCCESS_FIELD_ORDER,
    base_meta,
    error,
    error_response,
    success,
    success_result,
)


class SampleData(BaseModel):
    id: int
    name: str


def test_base_meta_generates_request_id_and_timestamp():
    meta = base_meta()

    assert "request_id" in meta
    assert "timestamp" in meta
    uuid.UUID(meta["request_id"])
    assert meta["timestamp"].endswith("+00:00")


def test_base_meta_preserves_request_id():
    meta = base_meta(request_id="fixed-request-id")

    assert meta["request_id"] == "fixed-request-id"
    assert "timestamp" in meta


def test_success_defaults():
    body = success()

    assert list(body.keys()) == list(SUCCESS_FIELD_ORDER)
    assert body["success"] is True
    assert body["status_code"] == 200
    assert body["message"] == "Success"
    assert body["data"] is None
    assert body["meta"] is None
    assert body["next_step"] is None
    assert body["links"] is None
    assert "request_id" in body
    assert "timestamp" in body


def test_success_with_custom_fields():
    body = success(
        data={"id": 1},
        message="Created",
        status_code=201,
        meta={"page": 1},
        next_step={"action": "view", "url": "/items/1"},
        links={"self": "/items/1"},
        request_id="req-123",
    )

    assert body["success"] is True
    assert body["status_code"] == 201
    assert body["message"] == "Created"
    assert body["data"] == {"id": 1}
    assert body["meta"] == {"page": 1}
    assert body["next_step"] == {"action": "view", "url": "/items/1"}
    assert body["links"] == {"self": "/items/1"}
    assert body["request_id"] == "req-123"


def test_error_defaults():
    body = error()

    assert list(body.keys()) == list(ERROR_FIELD_ORDER)
    assert body["success"] is False
    assert body["status_code"] == 500
    assert body["message"] == "Something went wrong"
    assert body["code"] is None
    assert body["errors"] is None
    assert body["meta"] is None
    assert body["next_step"] is None
    assert body["links"] is None
    assert "request_id" in body
    assert "timestamp" in body


def test_error_with_custom_fields():
    body = error(
        message="Not found",
        status_code=404,
        code="NOT_FOUND",
        errors=[{"field": "id", "message": "Invalid"}],
        request_id="err-456",
    )

    assert body["success"] is False
    assert body["status_code"] == 404
    assert body["message"] == "Not found"
    assert body["code"] == "NOT_FOUND"
    assert body["errors"] == [{"field": "id", "message": "Invalid"}]
    assert body["request_id"] == "err-456"


def test_success_result_injects_request_id_and_serializes_data():
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
        "query_string": b"",
    }
    request = Request(scope)
    request.state.request_id = "scoped-request-id"

    body = success_result(
        request,
        data=SampleData(id=1, name="Alice"),
        message="OK",
    )

    assert body["request_id"] == "scoped-request-id"
    assert body["data"] == {"id": 1, "name": "Alice"}


def test_error_response_wraps_envelope():
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
        "query_string": b"",
    }
    request = Request(scope)
    request.state.request_id = "error-request-id"

    response = error_response(
        request,
        message="Forbidden",
        status_code=403,
        code="FORBIDDEN",
    )

    assert response.status_code == 403
    body = json.loads(response.body)
    assert list(body.keys()) == list(ERROR_FIELD_ORDER)
    assert body["success"] is False
    assert body["message"] == "Forbidden"
    assert body["code"] == "FORBIDDEN"
    assert body["request_id"] == "error-request-id"
