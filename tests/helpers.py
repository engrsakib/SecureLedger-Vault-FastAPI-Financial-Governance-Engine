from app.core.response import ERROR_FIELD_ORDER, SUCCESS_FIELD_ORDER


def assert_success_envelope(body: dict, *, status_code: int | None = None) -> None:
    assert list(body.keys()) == list(SUCCESS_FIELD_ORDER)
    assert body["success"] is True
    if status_code is not None:
        assert body["status_code"] == status_code
    assert isinstance(body["message"], str)
    assert body["request_id"]
    assert body["timestamp"]


def assert_error_envelope(body: dict, *, status_code: int | None = None) -> None:
    assert list(body.keys()) == list(ERROR_FIELD_ORDER)
    assert body["success"] is False
    if status_code is not None:
        assert body["status_code"] == status_code
    assert isinstance(body["message"], str)
    assert body["request_id"]
    assert body["timestamp"]


def get_success_data(response):
    body = response.json()
    assert_success_envelope(body, status_code=response.status_code)
    return body["data"]


def get_error_body(response):
    body = response.json()
    assert_error_envelope(body, status_code=response.status_code)
    return body
