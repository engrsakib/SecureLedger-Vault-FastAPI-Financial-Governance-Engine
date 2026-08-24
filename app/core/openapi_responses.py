from app.schemas.envelope import ApiErrorResponse

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


def error_responses(*status_codes: int) -> dict[int, dict]:
    return {
        code: {
            "model": ApiErrorResponse,
            "description": ERROR_DESCRIPTIONS.get(code, "Error response"),
        }
        for code in status_codes
    }


def merge_openapi_error_responses(
    operation_responses: dict,
    status_codes: tuple[int, ...],
) -> None:
    """Ensure every operation documents standard error envelopes in OpenAPI."""
    for code in status_codes:
        key = str(code)
        if key in operation_responses:
            continue
        operation_responses[key] = {
            "description": ERROR_DESCRIPTIONS.get(code, "Error response"),
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ApiErrorResponse"}
                }
            },
        }
