"""
Transaction endpoint tests — unit & integration coverage.

Required (Module 24 — 10 marks):
  1. Get transaction test       — list all transactions
  2. Get specific transaction   — fetch by ID
  3. Create transaction test    — POST new transaction
  4. Update transaction test    — PUT existing transaction
"""

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Shared payloads
# ---------------------------------------------------------------------------

EXPENSE_PAYLOAD = {
    "title": "Groceries",
    "amount": 150.0,
    "type": "expense",
    "category": "Food",
    "date": "2026-01-15",
}

INCOME_PAYLOAD = {
    "title": "Salary",
    "amount": 5000.0,
    "type": "income",
    "category": "Work",
    "date": "2026-01-01",
}


def create_transaction(client: TestClient, headers: dict, payload: dict | None = None) -> dict:
    """Helper: create a transaction and return the response JSON."""
    response = client.post(
        "/transactions",
        json=payload or EXPENSE_PAYLOAD,
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


# =============================================================================
# 1. CREATE TRANSACTION TESTS
# =============================================================================


class TestCreateTransaction:
    """POST /transactions — create a new income or expense record."""

    def test_create_transaction_success(self, client, auth_headers):
        response = client.post("/transactions", json=INCOME_PAYLOAD, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == INCOME_PAYLOAD["title"]
        assert data["amount"] == INCOME_PAYLOAD["amount"]
        assert data["type"] == INCOME_PAYLOAD["type"]
        assert data["category"] == INCOME_PAYLOAD["category"]
        assert data["date"] == INCOME_PAYLOAD["date"]
        assert data["id"] is not None
        assert data["owner_id"] is not None

    def test_create_transaction_assigns_owner_from_jwt(self, client, auth_headers):
        data = create_transaction(client, auth_headers, EXPENSE_PAYLOAD)
        assert isinstance(data["owner_id"], int)
        assert data["owner_id"] > 0

    def test_create_transaction_requires_authentication(self, client):
        response = client.post("/transactions", json=EXPENSE_PAYLOAD)
        assert response.status_code == 401

    def test_create_transaction_rejects_invalid_amount(self, client, auth_headers):
        invalid_payload = {**EXPENSE_PAYLOAD, "amount": -50.0}
        response = client.post("/transactions", json=invalid_payload, headers=auth_headers)
        assert response.status_code == 422

    def test_create_transaction_rejects_invalid_type(self, client, auth_headers):
        invalid_payload = {**EXPENSE_PAYLOAD, "type": "invalid"}
        response = client.post("/transactions", json=invalid_payload, headers=auth_headers)
        assert response.status_code == 422


# =============================================================================
# 2. GET ALL TRANSACTIONS TESTS
# =============================================================================


class TestGetTransactions:
    """GET /transactions — retrieve the list of transactions for the current user."""

    def test_get_transactions_empty_list(self, client, auth_headers):
        response = client.get("/transactions", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_get_all_transactions_returns_user_records(
        self, client, auth_headers, sample_transaction
    ):
        create_transaction(client, auth_headers, INCOME_PAYLOAD)

        response = client.get("/transactions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        titles = {item["title"] for item in data}
        assert sample_transaction["title"] in titles
        assert INCOME_PAYLOAD["title"] in titles

    def test_get_transactions_returns_full_response_shape(self, client, auth_headers):
        create_transaction(client, auth_headers, EXPENSE_PAYLOAD)

        data = client.get("/transactions", headers=auth_headers).json()
        record = data[0]

        assert set(record.keys()) == {
            "id", "title", "amount", "type", "category", "date", "owner_id"
        }

    def test_get_transactions_requires_authentication(self, client):
        response = client.get("/transactions")
        assert response.status_code == 401


# =============================================================================
# 3. GET SPECIFIC TRANSACTION TESTS
# =============================================================================


class TestGetTransactionById:
    """GET /transactions/{transaction_id} — fetch a single transaction by ID."""

    def test_get_transaction_by_id_success(self, client, auth_headers, sample_transaction):
        transaction_id = sample_transaction["id"]

        response = client.get(f"/transactions/{transaction_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == transaction_id
        assert data["title"] == sample_transaction["title"]
        assert data["amount"] == sample_transaction["amount"]
        assert data["type"] == sample_transaction["type"]
        assert data["category"] == sample_transaction["category"]
        assert data["date"] == sample_transaction["date"]
        assert data["owner_id"] == sample_transaction["owner_id"]

    def test_get_transaction_by_id_not_found(self, client, auth_headers):
        response = client.get("/transactions/99999", headers=auth_headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Transaction not found"

    def test_get_transaction_by_id_requires_authentication(self, client):
        response = client.get("/transactions/1")
        assert response.status_code == 401

    def test_cannot_access_other_users_transaction(
        self, client, auth_headers, sample_transaction
    ):
        client.post(
            "/auth/register",
            json={
                "username": "otheruser",
                "email": "other@example.com",
                "password": "otherpassword123",
            },
        )
        other_login = client.post(
            "/auth/login",
            json={
                "username": "otheruser",
                "password": "otherpassword123",
                "device_id": "other-device-001",
            },
        )
        other_headers = {
            "Authorization": f"Bearer {other_login.json()['access_token']}"
        }

        response = client.get(
            f"/transactions/{sample_transaction['id']}",
            headers=other_headers,
        )
        assert response.status_code == 404


# =============================================================================
# 4. UPDATE TRANSACTION TESTS
# =============================================================================


class TestUpdateTransaction:
    """PUT /transactions/{transaction_id} — update an existing transaction."""

    def test_update_transaction_partial_fields(self, client, auth_headers, sample_transaction):
        transaction_id = sample_transaction["id"]

        response = client.put(
            f"/transactions/{transaction_id}",
            json={"title": "Updated Groceries", "amount": 200.0},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == transaction_id
        assert data["title"] == "Updated Groceries"
        assert data["amount"] == 200.0
        assert data["type"] == sample_transaction["type"]
        assert data["category"] == sample_transaction["category"]

    def test_update_transaction_persists_changes(self, client, auth_headers, sample_transaction):
        transaction_id = sample_transaction["id"]
        client.put(
            f"/transactions/{transaction_id}",
            json={"title": "Persisted Title", "category": "Shopping"},
            headers=auth_headers,
        )

        get_response = client.get(f"/transactions/{transaction_id}", headers=auth_headers)
        data = get_response.json()
        assert data["title"] == "Persisted Title"
        assert data["category"] == "Shopping"

    def test_update_transaction_all_fields(self, client, auth_headers, sample_transaction):
        transaction_id = sample_transaction["id"]
        updated = {
            "title": "Freelance Payment",
            "amount": 1200.0,
            "type": "income",
            "category": "Work",
            "date": "2026-02-01",
        }

        response = client.put(
            f"/transactions/{transaction_id}",
            json=updated,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == updated["title"]
        assert data["amount"] == updated["amount"]
        assert data["type"] == updated["type"]
        assert data["category"] == updated["category"]
        assert data["date"] == updated["date"]

    def test_update_transaction_not_found(self, client, auth_headers):
        response = client.put(
            "/transactions/99999",
            json={"title": "Ghost"},
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Transaction not found"

    def test_update_transaction_requires_authentication(self, client):
        response = client.put("/transactions/1", json={"title": "No Auth"})
        assert response.status_code == 401


# =============================================================================
# BONUS — DELETE & FILTER (beyond the 10-mark minimum)
# =============================================================================


class TestDeleteTransaction:
    """DELETE /transactions/{transaction_id} — remove a transaction."""

    def test_delete_transaction_success(self, client, auth_headers, sample_transaction):
        transaction_id = sample_transaction["id"]

        response = client.delete(f"/transactions/{transaction_id}", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["message"] == "Transaction deleted successfully"

        get_response = client.get(f"/transactions/{transaction_id}", headers=auth_headers)
        assert get_response.status_code == 404


class TestFilterTransactions:
    """GET/POST /transactions/filter — filter by type, category, and amount."""

    def test_filter_transactions_by_query_params(self, client, auth_headers):
        create_transaction(client, auth_headers, EXPENSE_PAYLOAD)
        create_transaction(client, auth_headers, INCOME_PAYLOAD)

        response = client.get(
            "/transactions/filter",
            params={"type": "expense", "category": "Food", "minimum_amount": 100},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == EXPENSE_PAYLOAD["title"]

    def test_filter_transactions_by_json_body(self, client, auth_headers):
        create_transaction(client, auth_headers, EXPENSE_PAYLOAD)
        create_transaction(client, auth_headers, INCOME_PAYLOAD)

        response = client.post(
            "/transactions/filter",
            json={"type": "income", "minimum_amount": 1000},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["type"] == "income"
