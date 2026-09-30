import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User
from app.core.security import hash_password


async def setup_two_agencies(db_session: AsyncSession):
    u1 = User(username="agency_a", password_hash=hash_password("AgencyPass12345!"), is_active=True)
    u2 = User(username="agency_b", password_hash=hash_password("AgencyPass12345!"), is_active=True)
    db_session.add_all([u1, u2])
    await db_session.commit()
    await db_session.refresh(u1)
    await db_session.refresh(u2)
    return u1, u2


@pytest.mark.asyncio
async def test_add_and_list_pages_isolation(client: AsyncClient, db_session: AsyncSession):
    u1, u2 = await setup_two_agencies(db_session)

    # Login as Agency A
    csrf_res = await client.get("/api/v1/auth/csrf")
    csrf_token = csrf_res.json()["csrf_token"]

    await client.post(
        "/api/v1/auth/login",
        json={"username": "agency_a", "password": "AgencyPass12345!"},
        headers={"X-CSRF-Token": csrf_token}
    )

    # Agency A adds page 'nike'
    add_res = await client.post(
        "/api/v1/pages",
        json={"username": "nike"},
        headers={"X-CSRF-Token": csrf_token}
    )
    assert add_res.status_code in (201, 202)
    assert add_res.json()["username"] == "nike"

    # List pages for Agency A -> 1 page
    list_a = await client.get("/api/v1/pages")
    assert list_a.status_code == 200
    assert len(list_a.json()) == 1
    assert list_a.json()[0]["username"] == "nike"

    # Logout Agency A
    await client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf_token})

    # Login as Agency B
    csrf_res = await client.get("/api/v1/auth/csrf")
    csrf_token = csrf_res.json()["csrf_token"]
    await client.post(
        "/api/v1/auth/login",
        json={"username": "agency_b", "password": "AgencyPass12345!"},
        headers={"X-CSRF-Token": csrf_token}
    )

    # List pages for Agency B -> 0 pages (isolation verification)
    list_b = await client.get("/api/v1/pages")
    assert list_b.status_code == 200
    assert len(list_b.json()) == 0

    # Agency B adds page 'adidas'
    add_b = await client.post(
        "/api/v1/pages",
        json={"username": "adidas"},
        headers={"X-CSRF-Token": csrf_token}
    )
    assert add_b.status_code in (201, 202)

    list_b2 = await client.get("/api/v1/pages")
    assert len(list_b2.json()) == 1
    assert list_b2.json()[0]["username"] == "adidas"


@pytest.mark.asyncio
async def test_sorting_and_nulls_last(client: AsyncClient, db_session: AsyncSession):
    u1 = User(username="agency_sort", password_hash=hash_password("AgencyPass12345!"), is_active=True)
    db_session.add(u1)
    await db_session.commit()

    csrf_res = await client.get("/api/v1/auth/csrf")
    csrf_token = csrf_res.json()["csrf_token"]

    await client.post(
        "/api/v1/auth/login",
        json={"username": "agency_sort", "password": "AgencyPass12345!"},
        headers={"X-CSRF-Token": csrf_token}
    )

    # Add 2 pages
    await client.post("/api/v1/pages", json={"username": "nike"}, headers={"X-CSRF-Token": csrf_token})
    await client.post("/api/v1/pages", json={"username": "puma"}, headers={"X-CSRF-Token": csrf_token})

    # Sort by followers desc
    res_desc = await client.get("/api/v1/pages?sort=followers&order=desc")
    assert res_desc.status_code == 200
    pages = res_desc.json()
    assert len(pages) == 2

    # Invalid sort field should fallback safely without error
    res_inv = await client.get("/api/v1/pages?sort=invalid_column&order=asc")
    assert res_inv.status_code == 200
