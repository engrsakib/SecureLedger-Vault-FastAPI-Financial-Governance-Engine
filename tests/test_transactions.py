def test_create_transaction(client, auth_headers):
    response = client.post(
        "/transactions",
        json={
            "title": "Salary",
            "amount": 5000.0,
            "type": "income",
            "category": "Work",
            "date": "2026-01-01",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Salary"
    assert data["amount"] == 5000.0
    assert data["type"] == "income"
    assert data["owner_id"] is not None


def test_get_all_transactions(client, auth_headers, sample_transaction):
    response = client.get("/transactions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == sample_transaction["title"]


def test_get_transaction_by_id(client, auth_headers, sample_transaction):
    transaction_id = sample_transaction["id"]
    response = client.get(
        f"/transactions/{transaction_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == transaction_id
    assert data["title"] == "Groceries"


def test_update_transaction(client, auth_headers, sample_transaction):
    transaction_id = sample_transaction["id"]
    response = client.put(
        f"/transactions/{transaction_id}",
        json={"title": "Updated Groceries", "amount": 200.0},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Groceries"
    assert data["amount"] == 200.0


def test_delete_transaction(client, auth_headers, sample_transaction):
    transaction_id = sample_transaction["id"]
    response = client.delete(
        f"/transactions/{transaction_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Transaction deleted successfully"

    get_response = client.get(
        f"/transactions/{transaction_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404


def test_cannot_access_other_users_transaction(client, auth_headers, sample_transaction):
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
        data={"username": "otheruser", "password": "otherpassword123"},
    )
    other_headers = {
        "Authorization": f"Bearer {other_login.json()['access_token']}"
    }

    transaction_id = sample_transaction["id"]
    response = client.get(
        f"/transactions/{transaction_id}",
        headers=other_headers,
    )
    assert response.status_code == 404


def test_filter_transactions(client, auth_headers):
    client.post(
        "/transactions",
        json={
            "title": "Lunch",
            "amount": 250.0,
            "type": "expense",
            "category": "Food",
            "date": "2026-01-10",
        },
        headers=auth_headers,
    )
    client.post(
        "/transactions",
        json={
            "title": "Bonus",
            "amount": 1000.0,
            "type": "income",
            "category": "Work",
            "date": "2026-01-20",
        },
        headers=auth_headers,
    )

    response = client.get(
        "/transactions/filter",
        params={"type": "expense", "category": "Food", "minimum_amount": 100},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Lunch"
