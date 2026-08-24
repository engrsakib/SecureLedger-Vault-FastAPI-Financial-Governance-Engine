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
    data = register_response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "hashed_password" not in data
    assert "password" not in data

    login_response = client.post(
        "/auth/login",
        json={
            "username": "newuser",
            "password": "securepassword123",
            "device_id": TEST_DEVICE_ID,
        },
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
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
    first = first_login.json()
    second = second_login.json()
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
    refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 200
    data = refresh_response.json()
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
    tokens = login_response.json()
    auth_headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    logout_response = client.post("/auth/logout", headers=auth_headers)
    assert logout_response.status_code == 200

    protected_response = client.get("/transactions", headers=auth_headers)
    assert protected_response.status_code == 401
