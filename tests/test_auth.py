TEST_DEVICE_ID = "test-device-auth-001"


def test_register_and_login(client, device_headers):
    headers = {**device_headers, "X-Device-ID": TEST_DEVICE_ID}
    register_response = client.post(
        "/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123",
        },
        headers=headers,
    )
    assert register_response.status_code == 201
    data = register_response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "hashed_password" not in data
    assert "password" not in data

    login_response = client.post(
        "/auth/login",
        data={"username": "newuser", "password": "securepassword123"},
        headers=headers,
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data["session_id"]
    assert token_data["device_id"] == TEST_DEVICE_ID


def test_same_device_returns_same_token(client, device_headers):
    headers = {**device_headers, "X-Device-ID": "shared-device-123"}
    client.post(
        "/auth/register",
        json={
            "username": "deviceuser",
            "email": "device@example.com",
            "password": "securepassword123",
        },
        headers=headers,
    )

    first_login = client.post(
        "/auth/login",
        data={"username": "deviceuser", "password": "securepassword123"},
        headers=headers,
    )
    second_login = client.post(
        "/auth/login",
        data={"username": "deviceuser", "password": "securepassword123"},
        headers=headers,
    )

    assert first_login.status_code == 200
    assert second_login.status_code == 200
    first = first_login.json()
    second = second_login.json()
    assert first["access_token"] == second["access_token"]
    assert first["refresh_token"] == second["refresh_token"]
    assert first["session_id"] == second["session_id"]


def test_refresh_token(client, device_headers):
    headers = {**device_headers, "X-Device-ID": "refresh-device-456"}
    client.post(
        "/auth/register",
        json={
            "username": "refreshuser",
            "email": "refresh@example.com",
            "password": "securepassword123",
        },
        headers=headers,
    )
    login_response = client.post(
        "/auth/login",
        data={"username": "refreshuser", "password": "securepassword123"},
        headers=headers,
    )
    refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
        headers=headers,
    )
    assert refresh_response.status_code == 200
    data = refresh_response.json()
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["device_id"] == "refresh-device-456"


def test_logout_revokes_token(client, device_headers):
    headers = {**device_headers, "X-Device-ID": "logout-device-789"}
    client.post(
        "/auth/register",
        json={
            "username": "logoutuser",
            "email": "logout@example.com",
            "password": "securepassword123",
        },
        headers=headers,
    )
    login_response = client.post(
        "/auth/login",
        data={"username": "logoutuser", "password": "securepassword123"},
        headers=headers,
    )
    tokens = login_response.json()
    auth_headers = {
        **headers,
        "Authorization": f"Bearer {tokens['access_token']}",
    }

    logout_response = client.post("/auth/logout", headers=auth_headers)
    assert logout_response.status_code == 200

    protected_response = client.get("/transactions", headers=auth_headers)
    assert protected_response.status_code == 401
