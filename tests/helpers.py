def get_success_data(response):
    body = response.json()
    assert body["success"] is True
    assert "request_id" in body
    assert "timestamp" in body
    return body["data"]


def get_error_body(response):
    body = response.json()
    assert body["success"] is False
    assert "request_id" in body
    assert "timestamp" in body
    return body
