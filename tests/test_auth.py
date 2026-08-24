from tests.helpers import get_error_body, get_success_data

TEST_DEVICE_ID = "test-device-auth-001"


def test_register_and_login(client):
    register_response = client.post(
        "/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123",
        },
    )
    assert register_response.status_code == 201
    register_body = register_response.json()
    assert register_body["success"] is True
    data = register_body["data"]
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "hashed_password" not in data
    assert "password" not in data
    assert register_body["links"] is not None
    assert register_body["next_step"] is not None

    login_response = client.post(
        "/auth/login",
        json={
            "username": "newuser",
            "password": "securepassword123",
            "device_id": TEST_DEVICE_ID,
        },
    )
    assert login_response.status_code == 200
    token_data = get_success_data(login_response)
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data["session_id"]
    assert token_data["device_id"] == TEST_DEVICE_ID


def test_same_device_returns_same_token(client):
    client.post(
        "/auth/register",
        json={
            "username": "deviceuser",
            "email": "device@example.com",
            "password": "securepassword123",
        },
    )

    login_payload = {
        "username": "deviceuser",
        "password": "securepassword123",
        "device_id": "shared-device-123",
    }
    first_login = client.post("/auth/login", json=login_payload)
    second_login = client.post("/auth/login", json=login_payload)

    assert first_login.status_code == 200
    assert second_login.status_code == 200
    first = get_success_data(first_login)
    second = get_success_data(second_login)
    assert first["access_token"] == second["access_token"]
    assert first["refresh_token"] == second["refresh_token"]
    assert first["session_id"] == second["session_id"]


def test_refresh_token(client):
    client.post(
        "/auth/register",
        json={
            "username": "refreshuser",
            "email": "refresh@example.com",
            "password": "securepassword123",
        },
    )
    login_response = client.post(
        "/auth/login",
        json={
            "username": "refreshuser",
            "password": "securepassword123",
            "device_id": "refresh-device-456",
        },
    )
    refresh_token = get_success_data(login_response)["refresh_token"]

    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 200
    data = get_success_data(refresh_response)
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["device_id"] == "refresh-device-456"


def test_logout_revokes_token(client):
    client.post(
        "/auth/register",
        json={
            "username": "logoutuser",
            "email": "logout@example.com",
            "password": "securepassword123",
        },
    )
    login_response = client.post(
        "/auth/login",
        json={
            "username": "logoutuser",
            "password": "securepassword123",
            "device_id": "logout-device-789",
        },
    )
    tokens = get_success_data(login_response)
    auth_headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    logout_response = client.post("/auth/logout", headers=auth_headers)
    assert logout_response.status_code == 200
    assert logout_response.json()["success"] is True

    protected_response = client.get("/transactions", headers=auth_headers)
    assert protected_response.status_code == 401
    error_body = get_error_body(protected_response)
    assert error_body["message"]
