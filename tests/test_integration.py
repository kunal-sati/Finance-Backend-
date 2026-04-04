def register_user(client, email: str, password: str = "Password@123"):
    return client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )


def login_user(client, email: str, password: str = "Password@123"):
    return client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_admin_and_token(client):
    register_user(client, "admin@example.com")
    login_resp = login_user(client, "admin@example.com")
    token = login_resp.json()["access_token"]
    return token


def test_role_based_access_control(client):
    admin_token = create_admin_and_token(client)

    create_analyst = client.post(
        "/users/",
        headers=auth_headers(admin_token),
        json={
            "email": "analyst@example.com",
            "password": "Password@123",
            "role": "analyst",
            "is_active": True,
        },
    )
    assert create_analyst.status_code == 201

    analyst_login = login_user(client, "analyst@example.com")
    analyst_token = analyst_login.json()["access_token"]

    forbidden_create = client.post(
        "/records/",
        headers=auth_headers(analyst_token),
        json={
            "amount": 100.5,
            "type": "income",
            "category": "Salary",
            "date": "2026-04-01",
            "description": "monthly salary",
        },
    )
    assert forbidden_create.status_code == 403

    viewer_create = client.post(
        "/users/",
        headers=auth_headers(admin_token),
        json={
            "email": "viewer@example.com",
            "password": "Password@123",
            "role": "viewer",
            "is_active": True,
        },
    )
    assert viewer_create.status_code == 201

    viewer_login = login_user(client, "viewer@example.com")
    viewer_token = viewer_login.json()["access_token"]

    viewer_records = client.get("/records/", headers=auth_headers(viewer_token))
    assert viewer_records.status_code == 403

    viewer_dashboard = client.get("/dashboard/summary", headers=auth_headers(viewer_token))
    assert viewer_dashboard.status_code == 200


def test_search_soft_delete_and_dashboard_exclusion(client):
    admin_token = create_admin_and_token(client)
    headers = auth_headers(admin_token)

    first_record = client.post(
        "/records/",
        headers=headers,
        json={
            "amount": 1000,
            "type": "income",
            "category": "Salary",
            "date": "2026-04-01",
            "description": "April salary payout",
        },
    )
    assert first_record.status_code == 201

    second_record = client.post(
        "/records/",
        headers=headers,
        json={
            "amount": 200,
            "type": "expense",
            "category": "Groceries",
            "date": "2026-04-02",
            "description": "Supermarket purchase",
        },
    )
    assert second_record.status_code == 201
    second_record_id = second_record.json()["id"]

    search_resp = client.get(
        "/records/",
        headers=headers,
        params={"search": "supermarket"},
    )
    assert search_resp.status_code == 200
    payload = search_resp.json()
    assert len(payload) == 1
    assert payload[0]["category"] == "Groceries"

    delete_resp = client.delete(f"/records/{second_record_id}", headers=headers)
    assert delete_resp.status_code == 204

    deleted_get = client.get(f"/records/{second_record_id}", headers=headers)
    assert deleted_get.status_code == 404

    summary_resp = client.get("/dashboard/summary", headers=headers)
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["total_income"] == 1000.0
    assert summary["total_expenses"] == 0.0
    assert summary["net_balance"] == 1000.0


def test_login_rate_limiting(client):
    register_resp = register_user(client, "limit@example.com")
    assert register_resp.status_code == 201

    for _ in range(5):
        resp = login_user(client, "limit@example.com", password="WrongPass@123")
        assert resp.status_code == 401

    blocked_resp = login_user(client, "limit@example.com", password="WrongPass@123")
    assert blocked_resp.status_code == 429
