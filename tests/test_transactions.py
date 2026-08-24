from fastapi.testclient import TestClient

from tests.helpers import get_error_body, get_success_data

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
    response = client.post(
        "/transactions",
        json=payload or EXPENSE_PAYLOAD,
        headers=headers,
    )
    assert response.status_code == 201
    return get_success_data(response)


class TestCreateTransaction:
    def test_create_transaction_success(self, client, auth_headers):
        response = client.post("/transactions", json=INCOME_PAYLOAD, headers=auth_headers)

        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        assert body["links"] is not None
        data = body["data"]
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
        assert get_error_body(response)["success"] is False

    def test_create_transaction_rejects_invalid_amount(self, client, auth_headers):
        invalid_payload = {**EXPENSE_PAYLOAD, "amount": -50.0}
        response = client.post("/transactions", json=invalid_payload, headers=auth_headers)
        assert response.status_code == 422
        assert get_error_body(response)["code"] == "VALIDATION_ERROR"

    def test_create_transaction_rejects_invalid_type(self, client, auth_headers):
        invalid_payload = {**EXPENSE_PAYLOAD, "type": "invalid"}
        response = client.post("/transactions", json=invalid_payload, headers=auth_headers)
        assert response.status_code == 422
        assert get_error_body(response)["code"] == "VALIDATION_ERROR"


class TestGetTransactions:
    def test_get_transactions_empty_list(self, client, auth_headers):
        response = client.get("/transactions", headers=auth_headers)

        assert response.status_code == 200
        body = response.json()
        assert body["data"] == []
        assert body["meta"]["total_items"] == 0
        assert body["meta"]["page"] == 1
        assert body["meta"]["page_size"] == 20

    def test_get_all_transactions_returns_user_records(
        self, client, auth_headers, sample_transaction
    ):
        create_transaction(client, auth_headers, INCOME_PAYLOAD)

        data = get_success_data(client.get("/transactions", headers=auth_headers))

        assert len(data) == 2
        titles = {item["title"] for item in data}
        assert sample_transaction["title"] in titles
        assert INCOME_PAYLOAD["title"] in titles

    def test_get_transactions_returns_full_response_shape(self, client, auth_headers):
        create_transaction(client, auth_headers, EXPENSE_PAYLOAD)

        data = get_success_data(client.get("/transactions", headers=auth_headers))
        record = data[0]

        assert set(record.keys()) == {
            "id", "title", "amount", "type", "category", "date", "owner_id"
        }

    def test_get_transactions_requires_authentication(self, client):
        response = client.get("/transactions")
        assert response.status_code == 401

    def test_get_transactions_pagination(self, client, auth_headers):
        for index in range(5):
            create_transaction(
                client,
                auth_headers,
                {
                    **EXPENSE_PAYLOAD,
                    "title": f"Expense {index}",
                    "amount": float(index + 1) * 10,
                },
            )

        response = client.get(
            "/transactions",
            params={"page": 2, "page_size": 2, "sort_by": "amount", "sort_order": "asc"},
            headers=auth_headers,
        )
        body = response.json()

        assert response.status_code == 200
        assert len(body["data"]) == 2
        assert body["meta"]["page"] == 2
        assert body["meta"]["page_size"] == 2
        assert body["meta"]["total_items"] == 5
        assert body["meta"]["total_pages"] == 3
        assert body["meta"]["has_next"] is True
        assert body["meta"]["has_previous"] is True
        assert body["data"][0]["amount"] == 30.0

    def test_get_transactions_search(self, client, auth_headers):
        create_transaction(client, auth_headers, EXPENSE_PAYLOAD)
        create_transaction(client, auth_headers, INCOME_PAYLOAD)

        data = get_success_data(
            client.get("/transactions", params={"search": "salary"}, headers=auth_headers)
        )

        assert len(data) == 1
        assert data[0]["title"] == INCOME_PAYLOAD["title"]

    def test_get_transactions_filter_and_sort(self, client, auth_headers):
        create_transaction(client, auth_headers, EXPENSE_PAYLOAD)
        create_transaction(client, auth_headers, INCOME_PAYLOAD)
        create_transaction(
            client,
            auth_headers,
            {
                **EXPENSE_PAYLOAD,
                "title": "Restaurant",
                "category": "Dining",
                "amount": 300.0,
            },
        )

        data = get_success_data(
            client.get(
                "/transactions",
                params={
                    "type": "expense",
                    "minimum_amount": 100,
                    "sort_by": "amount",
                    "sort_order": "desc",
                },
                headers=auth_headers,
            )
        )

        assert len(data) == 2
        assert data[0]["title"] == "Restaurant"
        assert data[1]["title"] == EXPENSE_PAYLOAD["title"]

    def test_get_transactions_invalid_pagination_returns_422(self, client, auth_headers):
        response = client.get(
            "/transactions",
            params={"page": 0, "page_size": 200},
            headers=auth_headers,
        )

        assert response.status_code == 422
        assert get_error_body(response)["code"] == "VALIDATION_ERROR"

    def test_get_transactions_date_range_filter(self, client, auth_headers):
        create_transaction(
            client,
            auth_headers,
            {**EXPENSE_PAYLOAD, "date": "2026-01-10"},
        )
        create_transaction(
            client,
            auth_headers,
            {**INCOME_PAYLOAD, "date": "2026-02-01"},
        )

        data = get_success_data(
            client.get(
                "/transactions",
                params={"date_from": "2026-01-01", "date_to": "2026-01-31"},
                headers=auth_headers,
            )
        )

        assert len(data) == 1
        assert data[0]["date"] == "2026-01-10"


class TestGetTransactionById:
    def test_get_transaction_by_id_success(self, client, auth_headers, sample_transaction):
        transaction_id = sample_transaction["id"]

        data = get_success_data(
            client.get(f"/transactions/{transaction_id}", headers=auth_headers)
        )

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
        assert get_error_body(response)["message"] == "Transaction not found"

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
            "Authorization": f"Bearer {get_success_data(other_login)['access_token']}"
        }

        response = client.get(
            f"/transactions/{sample_transaction['id']}",
            headers=other_headers,
        )
        assert response.status_code == 404


class TestUpdateTransaction:
    def test_update_transaction_partial_fields(self, client, auth_headers, sample_transaction):
        transaction_id = sample_transaction["id"]

        data = get_success_data(
            client.put(
                f"/transactions/{transaction_id}",
                json={"title": "Updated Groceries", "amount": 200.0},
                headers=auth_headers,
            )
        )

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

        data = get_success_data(
            client.get(f"/transactions/{transaction_id}", headers=auth_headers)
        )
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

        data = get_success_data(
            client.put(
                f"/transactions/{transaction_id}",
                json=updated,
                headers=auth_headers,
            )
        )

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
        assert get_error_body(response)["message"] == "Transaction not found"

    def test_update_transaction_requires_authentication(self, client):
        response = client.put("/transactions/1", json={"title": "No Auth"})
        assert response.status_code == 401

    def test_update_transaction_invalid_amount_returns_422(self, client, auth_headers, sample_transaction):
        response = client.put(
            f"/transactions/{sample_transaction['id']}",
            json={"amount": -10},
            headers=auth_headers,
        )

        assert response.status_code == 422
        assert get_error_body(response)["code"] == "VALIDATION_ERROR"


class TestDeleteTransaction:
    def test_delete_transaction_success(self, client, auth_headers, sample_transaction):
        transaction_id = sample_transaction["id"]

        response = client.delete(f"/transactions/{transaction_id}", headers=auth_headers)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["message"] == "Transaction deleted successfully"

        get_response = client.get(f"/transactions/{transaction_id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_transaction_not_found(self, client, auth_headers):
        response = client.delete("/transactions/99999", headers=auth_headers)

        assert response.status_code == 404
        assert get_error_body(response)["message"] == "Transaction not found"

    def test_delete_transaction_requires_authentication(self, client):
        response = client.delete("/transactions/1")
        assert response.status_code == 401


class TestFilterTransactions:
    def test_filter_transactions_by_query_params(self, client, auth_headers):
        create_transaction(client, auth_headers, EXPENSE_PAYLOAD)
        create_transaction(client, auth_headers, INCOME_PAYLOAD)

        data = get_success_data(
            client.get(
                "/transactions/filter",
                params={"type": "expense", "category": "Food", "minimum_amount": 100},
                headers=auth_headers,
            )
        )

        assert len(data) == 1
        assert data[0]["title"] == EXPENSE_PAYLOAD["title"]

    def test_filter_transactions_by_json_body(self, client, auth_headers):
        create_transaction(client, auth_headers, EXPENSE_PAYLOAD)
        create_transaction(client, auth_headers, INCOME_PAYLOAD)

        data = get_success_data(
            client.post(
                "/transactions/filter",
                json={"type": "income", "minimum_amount": 1000},
                headers=auth_headers,
            )
        )

        assert len(data) == 1
        assert data[0]["type"] == "income"

    def test_filter_transactions_query_requires_authentication(self, client):
        response = client.get("/transactions/filter", params={"type": "expense"})
        assert response.status_code == 401

    def test_filter_transactions_json_requires_authentication(self, client):
        response = client.post("/transactions/filter", json={"type": "income"})
        assert response.status_code == 401
