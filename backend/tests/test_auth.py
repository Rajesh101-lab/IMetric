import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User
from app.core.security import hash_password
from app.core.config import settings


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
        headers={"X-CSRF-Token": csrf_token, "Origin": "http://test"}
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
async def test_registration_requires_owner_approval(client: AsyncClient, db_session: AsyncSession):
    csrf_token = (await client.get("/api/v1/auth/csrf")).json()["csrf_token"]
    owner_name = settings.INITIAL_USER.strip().lower()
    owner = User(
        username=owner_name,
        password_hash=hash_password("OwnerAccountPass!2026"),
        is_active=True,
    )
    viewer = User(
        username="ordinary_viewer",
        password_hash=hash_password("ViewerAccountPass!2026"),
        is_active=True,
    )
    db_session.add_all([owner, viewer])
    await db_session.commit()

    weak_password = await client.post(
        "/api/v1/auth/register",
        json={"username": "new_agency", "password": "123456789012", "contact_email": "new@example.com"},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert weak_password.status_code == 422
    assert weak_password.json()["error"]["code"] == "WEAK_PASSWORD"

    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": " New_Agency ",
            "password": "CedarRiverSignal!2026",
            "contact_email": " Applicant@Example.com ",
        },
        headers={"X-CSRF-Token": csrf_token},
    )
    assert response.status_code == 202
    assert response.json()["username"] == "new_agency"
    assert response.json()["status"] == "pending"
    assert "session_id" not in client.cookies

    login_before_approval = await client.post(
        "/api/v1/auth/login",
        json={"username": "new_agency", "password": "CedarRiverSignal!2026"},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert login_before_approval.status_code == 401

    duplicate = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "new_agency",
            "password": "CedarRiverSignal!2026",
            "contact_email": "new@example.com",
        },
        headers={"X-CSRF-Token": csrf_token},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "REQUEST_PENDING"

    viewer_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "ordinary_viewer", "password": "ViewerAccountPass!2026"},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert viewer_login.status_code == 200
    assert viewer_login.json()["is_admin"] is False
    forbidden = await client.get("/api/v1/auth/registration-requests")
    assert forbidden.status_code == 403
    await client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf_token})

    owner_login = await client.post(
        "/api/v1/auth/login",
        json={"username": owner_name, "password": "OwnerAccountPass!2026"},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert owner_login.status_code == 200
    assert owner_login.json()["is_admin"] is True

    requests = await client.get("/api/v1/auth/registration-requests")
    assert requests.status_code == 200
    assert len(requests.json()) == 1
    request_item = requests.json()[0]
    assert request_item["username"] == "new_agency"
    assert request_item["contact_email"] == "applicant@example.com"
    assert "password_hash" not in request_item

    approved = await client.post(
        f"/api/v1/auth/registration-requests/{request_item['id']}/approve",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    await client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf_token})
    applicant_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "new_agency", "password": "CedarRiverSignal!2026"},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert applicant_login.status_code == 200
    assert applicant_login.json()["username"] == "new_agency"


@pytest.mark.asyncio
async def test_csrf_rejection(client: AsyncClient, db_session: AsyncSession):
    # Attempting POST without CSRF header should return 403
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "agency_test", "password": "SuperSecretAgency123!"}
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_csrf_rejects_foreign_origin(client: AsyncClient, db_session: AsyncSession):
    csrf_res = await client.get("/api/v1/auth/csrf")
    csrf_token = csrf_res.json()["csrf_token"]

    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "agency_test", "password": "SuperSecretAgency123!"},
        headers={"X-CSRF-Token": csrf_token, "Origin": "https://attacker.example"}
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "CSRF_ORIGIN_FORBIDDEN"


async def test_csrf_accepts_app_vercel_preview_origin(client: AsyncClient, db_session: AsyncSession):
    csrf_resp = await client.get("/api/v1/auth/csrf")
    csrf_token = csrf_resp.json()["csrf_token"]

    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "missing-user", "password": "not-a-real-password"},
        headers={
            "X-CSRF-Token": csrf_token,
            "Origin": "https://i-metric-ifry3aynw-im-etric.vercel.app",
        },
    )

    assert response.status_code == 401


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
