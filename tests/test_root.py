from tests.helpers import assert_success_envelope, get_success_data


def test_root_returns_welcome_envelope(client):
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert_success_envelope(body, status_code=200)
    assert body["message"]
    assert body["data"]["project"] == "SecureLedger Vault"
    assert body["data"]["version"] == "1.2.0"
    assert "swagger_ui" in body["data"]["documentation"]
    assert "health" in body["data"]["system"]
    assert body["data"]["developer"]["username"] == "engrsakib"
    assert body["links"] is not None
    assert body["next_step"] is not None


def test_health_returns_ok_envelope(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert_success_envelope(body, status_code=200)
    assert body["data"]["status"] == "ok"
    assert body["data"]["redis"] in {"connected", "disconnected"}
