from tests.helpers import get_error_body, get_success_data

TEST_DEVICE_ID = "test-device-auth-001"

REGISTER_PAYLOAD = {
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "securepassword123",
}


def register_user(client, payload: dict | None = None):
    return client.post("/auth/register", json=payload or REGISTER_PAYLOAD)


def login_user(client, username: str, password: str, device_id: str | None = TEST_DEVICE_ID):
    payload = {"username": username, "password": password}
    if device_id is not None:
        payload["device_id"] = device_id
    return client.post("/auth/login", json=payload)


class TestRegister:
    def test_register_and_login(self, client):
        register_response = register_user(client)
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

        login_response = login_user(client, "newuser", "securepassword123")
        assert login_response.status_code == 200
        token_data = get_success_data(login_response)
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert token_data["token_type"] == "bearer"
        assert token_data["session_id"]
        assert token_data["device_id"] == TEST_DEVICE_ID

    def test_register_duplicate_username(self, client):
        register_user(
            client,
            {
                "username": "duplicate",
                "email": "first@example.com",
                "password": "securepassword123",
            },
        )
        response = register_user(
            client,
            {
                "username": "duplicate",
                "email": "second@example.com",
                "password": "securepassword123",
            },
        )

        assert response.status_code == 400
        error = get_error_body(response)
        assert error["message"] == "Username already registered"

    def test_register_duplicate_email(self, client):
        register_user(
            client,
            {
                "username": "userone",
                "email": "shared@example.com",
                "password": "securepassword123",
            },
        )
        response = register_user(
            client,
            {
                "username": "usertwo",
                "email": "shared@example.com",
                "password": "securepassword123",
            },
        )

        assert response.status_code == 400
        error = get_error_body(response)
        assert error["message"] == "Email already registered"

    def test_register_validation_error(self, client):
        response = client.post(
            "/auth/register",
            json={"username": "bad", "email": "not-an-email", "password": "short"},
        )

        assert response.status_code == 422
        error = get_error_body(response)
        assert error["code"] == "VALIDATION_ERROR"
        assert error["errors"]


class TestLogin:
    def test_same_device_returns_same_token(self, client):
        register_user(
            client,
            {
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

    def test_login_wrong_password(self, client):
        register_user(
            client,
            {
                "username": "loginfail",
                "email": "loginfail@example.com",
                "password": "securepassword123",
            },
        )
        response = login_user(client, "loginfail", "wrongpassword")

        assert response.status_code == 401
        error = get_error_body(response)
        assert error["message"] == "Incorrect username or password"

    def test_login_unknown_user(self, client):
        response = login_user(client, "ghost", "securepassword123")

        assert response.status_code == 401
        error = get_error_body(response)
        assert error["message"] == "Incorrect username or password"

    def test_login_validation_error(self, client):
        response = client.post("/auth/login", json={"username": "onlyusername"})

        assert response.status_code == 422
        error = get_error_body(response)
        assert error["code"] == "VALIDATION_ERROR"


class TestRefresh:
    def test_refresh_token_success(self, client):
        register_user(
            client,
            {
                "username": "refreshuser",
                "email": "refresh@example.com",
                "password": "securepassword123",
            },
        )
        login_response = login_user(
            client, "refreshuser", "securepassword123", device_id="refresh-device-456"
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

    def test_refresh_invalid_token(self, client):
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "not-a-valid-token"},
        )

        assert response.status_code == 401
        error = get_error_body(response)
        assert error["message"]

    def test_refresh_revoked_after_logout(self, client):
        register_user(
            client,
            {
                "username": "revokeuser",
                "email": "revoke@example.com",
                "password": "securepassword123",
            },
        )
        login_response = login_user(
            client, "revokeuser", "securepassword123", device_id="revoke-device"
        )
        tokens = get_success_data(login_response)
        auth_headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        logout_response = client.post("/auth/logout", headers=auth_headers)
        assert logout_response.status_code == 200

        refresh_response = client.post(
            "/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert refresh_response.status_code == 401
        assert get_error_body(refresh_response)["message"]


class TestLogout:
    def test_logout_revokes_token(self, client):
        register_user(
            client,
            {
                "username": "logoutuser",
                "email": "logout@example.com",
                "password": "securepassword123",
            },
        )
        login_response = login_user(
            client, "logoutuser", "securepassword123", device_id="logout-device-789"
        )
        tokens = get_success_data(login_response)
        auth_headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        logout_response = client.post("/auth/logout", headers=auth_headers)
        assert logout_response.status_code == 200
        body = logout_response.json()
        assert body["success"] is True
        assert body["data"]["message"] == "Logged out successfully"

        protected_response = client.get("/transactions", headers=auth_headers)
        assert protected_response.status_code == 401
        error_body = get_error_body(protected_response)
        assert error_body["message"]

    def test_logout_requires_authentication(self, client):
        response = client.post("/auth/logout")

        assert response.status_code == 401
        assert get_error_body(response)["success"] is False
