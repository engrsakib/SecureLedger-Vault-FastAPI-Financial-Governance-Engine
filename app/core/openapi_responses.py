from copy import deepcopy
from typing import Any

from app.schemas.envelope import (
    ERROR_ENVELOPE_EXAMPLE,
    REQUEST_ID_EXAMPLE,
    TIMESTAMP_EXAMPLE,
    ApiErrorResponse,
    ApiMeta,
    NextStep,
    ValidationErrorItem,
)

ERROR_DESCRIPTIONS: dict[int, str] = {
    400: "Bad request — duplicate user, invalid input, or business rule violation",
    401: "Unauthorized — missing, expired, or revoked JWT",
    404: "Not found — resource does not exist or is not owned by the current user",
    422: "Validation error — invalid request body or query parameters",
    429: "Too many requests — rate limit exceeded",
    500: "Internal server error — unexpected server failure",
    503: "Service unavailable — dependency (e.g. Redis) temporarily unavailable",
}

PUBLIC_ERRORS = (400, 422, 429, 500, 503)
AUTH_ERRORS = (400, 401, 422, 429, 500, 503)
PROTECTED_ERRORS = (401, 404, 422, 429, 500, 503)

REF_TEMPLATE = "#/components/schemas/{model}"


def _base_error_example(status_code: int, message: str, code: str | None = None) -> dict[str, Any]:
    example = deepcopy(ERROR_ENVELOPE_EXAMPLE)
    example.update(
        {
            "status_code": status_code,
            "message": message,
            "code": code,
            "request_id": REQUEST_ID_EXAMPLE,
            "timestamp": TIMESTAMP_EXAMPLE,
        }
    )
    return example


ERROR_EXAMPLES: dict[int, dict[str, Any]] = {
    400: _base_error_example(400, "Username already registered"),
    401: _base_error_example(401, "Could not validate credentials"),
    404: _base_error_example(404, "Transaction not found"),
    422: {
        **_base_error_example(422, "Validation error", "VALIDATION_ERROR"),
        "errors": [
            {
                "type": "missing",
                "loc": ["body", "username"],
                "msg": "Field required",
                "input": None,
            }
        ],
    },
    429: _base_error_example(429, "Rate limit exceeded", "RATE_LIMIT_EXCEEDED"),
    500: _base_error_example(500, "Something went wrong", "INTERNAL_SERVER_ERROR"),
    503: _base_error_example(503, "Service temporarily unavailable", "SERVICE_UNAVAILABLE"),
}


def build_error_response_content(status_code: int) -> dict[str, Any]:
    return {
        "application/json": {
            "schema": {"$ref": "#/components/schemas/ApiErrorResponse"},
            "example": ERROR_EXAMPLES.get(
                status_code,
                _base_error_example(status_code, ERROR_DESCRIPTIONS.get(status_code, "Error")),
            ),
        }
    }


def error_responses(*status_codes: int) -> dict[int, dict]:
    return {
        code: {
            "model": ApiErrorResponse,
            "description": ERROR_DESCRIPTIONS.get(code, "Error response"),
            "content": build_error_response_content(code),
        }
        for code in status_codes
    }


def merge_openapi_error_responses(
    operation_responses: dict,
    status_codes: tuple[int, ...],
) -> None:
    """Ensure every operation documents the unified error envelope in OpenAPI."""
    for code in status_codes:
        operation_responses[str(code)] = {
            "description": ERROR_DESCRIPTIONS.get(code, "Error response"),
            "content": build_error_response_content(code),
        }


def patch_openapi_envelope_schemas(openapi_schema: dict[str, Any]) -> None:
    """Ensure shared envelope component schemas are fully defined in OpenAPI."""
    components = openapi_schema.setdefault("components", {})
    schemas = components.setdefault("schemas", {})

    schemas["ApiErrorResponse"] = ApiErrorResponse.model_json_schema(
        ref_template=REF_TEMPLATE
    )
    schemas["ValidationErrorItem"] = ValidationErrorItem.model_json_schema(
        ref_template=REF_TEMPLATE
    )
    schemas["NextStep"] = NextStep.model_json_schema(ref_template=REF_TEMPLATE)
    schemas["ApiMeta"] = ApiMeta.model_json_schema(ref_template=REF_TEMPLATE)
