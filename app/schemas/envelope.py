from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")

REQUEST_ID_EXAMPLE = "550e8400-e29b-41d4-a716-446655440000"
TIMESTAMP_EXAMPLE = "2026-08-24T14:30:00.000000+00:00"


class NextStep(BaseModel):
    action: str = Field(..., description="Suggested next action", examples=["login"])
    url: str = Field(..., description="URL for the next action", examples=["/auth/login"])


class ValidationErrorItem(BaseModel):
    type: str = Field(..., description="Error type", examples=["missing"])
    loc: list[str | int] = Field(
        ..., description="Location of the error", examples=[["body", "username"]]
    )
    msg: str = Field(..., description="Error message", examples=["Field required"])
    input: Any | None = Field(default=None, description="Invalid input value")


class ApiMeta(BaseModel):
    model_config = ConfigDict(extra="allow")

    page: int | None = Field(default=None, description="Current page number", examples=[1])
    page_size: int | None = Field(default=None, description="Items per page", examples=[20])
    total_items: int | None = Field(default=None, description="Total matching records", examples=[45])
    total_pages: int | None = Field(default=None, description="Total pages", examples=[3])
    has_next: bool | None = Field(default=None, description="Next page exists", examples=[True])
    has_previous: bool | None = Field(default=None, description="Previous page exists", examples=[False])
    sort_by: str | None = Field(default=None, description="Applied sort field", examples=["date"])
    sort_order: str | None = Field(default=None, description="Applied sort order", examples=["desc"])
    filters: dict[str, Any] | None = Field(
        default=None,
        description="Applied filters",
        examples=[{"type": "expense", "search": "food"}],
    )


ENVELOPE_EXAMPLE = {
    "success": True,
    "status_code": 200,
    "message": "Success",
    "data": None,
    "meta": None,
    "next_step": {"action": "login", "url": "https://example.com/auth/login"},
    "links": {"login": "https://example.com/auth/login"},
    "request_id": REQUEST_ID_EXAMPLE,
    "timestamp": TIMESTAMP_EXAMPLE,
}

ERROR_ENVELOPE_EXAMPLE = {
    "success": False,
    "status_code": 404,
    "message": "Transaction not found",
    "code": None,
    "errors": None,
    "meta": None,
    "next_step": None,
    "links": None,
    "request_id": REQUEST_ID_EXAMPLE,
    "timestamp": TIMESTAMP_EXAMPLE,
}


class ApiSuccessResponse(BaseModel, Generic[T]):
    """Unified success envelope returned by every API route."""

    model_config = ConfigDict(json_schema_extra={"example": ENVELOPE_EXAMPLE})

    success: Literal[True] = Field(True, description="Always `true` for successful responses")
    status_code: int = Field(..., description="HTTP status code (mirrored in the JSON body)")
    message: str = Field(..., description="Human-readable success message")
    data: T | None = Field(None, description="Endpoint-specific payload")
    meta: ApiMeta | dict[str, Any] | None = Field(
        None, description="Optional pagination or extra metadata"
    )
    next_step: NextStep | None = Field(None, description="Suggested next action")
    links: dict[str, str] | None = Field(None, description="Related HATEOAS-style resource URLs")
    request_id: str = Field(..., description="Unique request ID (also sent as X-Request-ID)")
    timestamp: str = Field(..., description="ISO-8601 UTC response timestamp")


class ApiErrorResponse(BaseModel):
    """Unified error envelope returned by handlers and global exception handlers."""

    model_config = ConfigDict(json_schema_extra={"example": ERROR_ENVELOPE_EXAMPLE})

    success: Literal[False] = Field(False, description="Always `false` for error responses")
    status_code: int = Field(..., description="HTTP status code (mirrored in the JSON body)")
    message: str = Field(..., description="Human-readable error message")
    code: str | None = Field(
        None,
        description="Machine-readable error code (e.g. VALIDATION_ERROR, RATE_LIMIT_EXCEEDED)",
    )
    errors: list[ValidationErrorItem] | None = Field(
        None, description="Validation or field-level error details"
    )
    meta: ApiMeta | dict[str, Any] | None = Field(None, description="Optional extra error context")
    next_step: NextStep | None = Field(None, description="Suggested recovery action")
    links: dict[str, str] | None = Field(None, description="Related resource URLs")
    request_id: str = Field(..., description="Unique request ID (also sent as X-Request-ID)")
    timestamp: str = Field(..., description="ISO-8601 UTC response timestamp")
