import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User
from app.core.security import hash_password


@pytest.mark.asyncio
async def test_auth_flow(client: AsyncClient, db_session: AsyncSession):
    # 1. Create a test user in DB
    user = User(
        username="agency_test",
        password_hash=hash_password("SuperSecretAgency123!"),
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()

    # 2. Get CSRF token
    csrf_res = await client.get("/api/v1/auth/csrf")
    assert csrf_res.status_code == 200
    csrf_token = csrf_res.json()["csrf_token"]

    # 3. Unauthenticated GET /auth/me -> 401
    me_unauth = await client.get("/api/v1/auth/me")
    assert me_unauth.status_code == 401

    # 4. Login with invalid password -> 401
    login_fail = await client.post(
        "/api/v1/auth/login",
        json={"username": "agency_test", "password": "WrongPassword123!"},
        headers={"X-CSRF-Token": csrf_token}
    )
    assert login_fail.status_code == 401
    assert login_fail.json()["error"]["message"] == "Invalid Agency ID or password."

    # 5. Successful login
    login_success = await client.post(
        "/api/v1/auth/login",
        json={"username": "agency_test", "password": "SuperSecretAgency123!"},
        headers={"X-CSRF-Token": csrf_token}
    )
    assert login_success.status_code == 200
    assert login_success.json()["username"] == "agency_test"
    assert "session_id" in client.cookies or "__Host-session_id" in client.cookies

    # 6. Authenticated GET /auth/me -> 200
    me_auth = await client.get("/api/v1/auth/me")
    assert me_auth.status_code == 200
    assert me_auth.json()["username"] == "agency_test"

    # 7. Logout
    logout_res = await client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": csrf_token}
    )
    assert logout_res.status_code == 200

    # 8. Post-logout GET /auth/me -> 401
    me_post_logout = await client.get("/api/v1/auth/me")
    assert me_post_logout.status_code == 401


@pytest.mark.asyncio
async def test_csrf_rejection(client: AsyncClient, db_session: AsyncSession):
    # Attempting POST without CSRF header should return 403
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "agency_test", "password": "SuperSecretAgency123!"}
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_lockout_after_five_failures(client: AsyncClient, db_session: AsyncSession):
    user = User(
        username="lockout_agency",
        password_hash=hash_password("SuperSecretAgency123!"),
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()

    csrf_res = await client.get("/api/v1/auth/csrf")
    csrf_token = csrf_res.json()["csrf_token"]

    # Fail 5 times
    for _ in range(5):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "lockout_agency", "password": "WrongPassword123!"},
            headers={"X-CSRF-Token": csrf_token}
        )
        assert resp.status_code == 401

    # 6th attempt with CORRECT password should fail because account is locked
    resp_locked = await client.post(
        "/api/v1/auth/login",
        json={"username": "lockout_agency", "password": "SuperSecretAgency123!"},
        headers={"X-CSRF-Token": csrf_token}
    )
    assert resp_locked.status_code == 401
    assert resp_locked.json()["error"]["message"] == "Invalid Agency ID or password."
