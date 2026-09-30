import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User, Page
from app.core.security import hash_password


@pytest.mark.asyncio
async def test_single_page_refresh_and_cooldown(client: AsyncClient, db_session: AsyncSession):
    user = User(username="agency_refresh", password_hash=hash_password("AgencyPass12345!"), is_active=True)
    db_session.add(user)
    await db_session.commit()

    csrf_res = await client.get("/api/v1/auth/csrf")
    csrf_token = csrf_res.json()["csrf_token"]

    await client.post(
        "/api/v1/auth/login",
        json={"username": "agency_refresh", "password": "AgencyPass12345!"},
        headers={"X-CSRF-Token": csrf_token}
    )

    # Add page
    add_res = await client.post("/api/v1/pages", json={"username": "nike"}, headers={"X-CSRF-Token": csrf_token})
    page_id = add_res.json()["id"]

    # Mark page as refreshed now so 60s cooldown is triggered
    await db_session.execute(
        update(Page)
        .where(Page.id == page_id)
        .values(last_refreshed_at=datetime.now(timezone.utc))
    )
    await db_session.commit()

    # Immediate refresh should trigger 60s cooldown (429)
    refresh_cooldown = await client.post(
        f"/api/v1/pages/{page_id}/refresh",
        headers={"X-CSRF-Token": csrf_token}
    )
    assert refresh_cooldown.status_code == 429
    assert "Please wait a moment" in refresh_cooldown.json()["error"]["message"]


@pytest.mark.asyncio
async def test_refresh_all_job(client: AsyncClient, db_session: AsyncSession):
    user = User(username="agency_ref_all", password_hash=hash_password("AgencyPass12345!"), is_active=True)
    db_session.add(user)
    await db_session.commit()

    csrf_res = await client.get("/api/v1/auth/csrf")
    csrf_token = csrf_res.json()["csrf_token"]

    await client.post(
        "/api/v1/auth/login",
        json={"username": "agency_ref_all", "password": "AgencyPass12345!"},
        headers={"X-CSRF-Token": csrf_token}
    )

    # Add pages
    await client.post("/api/v1/pages", json={"username": "nike"}, headers={"X-CSRF-Token": csrf_token})
    await client.post("/api/v1/pages", json={"username": "adidas"}, headers={"X-CSRF-Token": csrf_token})

    # Trigger refresh-all
    ref_all = await client.post("/api/v1/pages/refresh-all", headers={"X-CSRF-Token": csrf_token})
    assert ref_all.status_code == 202
    job_id = ref_all.json()["job_id"]
    assert ref_all.json()["total"] == 2

    # Poll status
    status_res = await client.get(f"/api/v1/pages/refresh-all/{job_id}")
    assert status_res.status_code == 200
    assert status_res.json()["job_id"] == job_id
