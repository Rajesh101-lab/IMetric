import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.models import User, Page, PageSnapshot, RefreshJob
from app.core.security import hash_password
from app.services.refresh_jobs import prune_refresh_history


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
    assert ref_all.json()["status"] == "queued"

    current_res = await client.get("/api/v1/pages/refresh-all/current")
    assert current_res.status_code == 200
    assert current_res.json()["job_id"] == job_id

    duplicate = await client.post("/api/v1/pages/refresh-all", headers={"X-CSRF-Token": csrf_token})
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "JOB_IN_PROGRESS"

    # Poll status
    status_res = await client.get(f"/api/v1/pages/refresh-all/{job_id}")
    assert status_res.status_code == 200
    assert status_res.json()["job_id"] == job_id


@pytest.mark.asyncio
async def test_prune_refresh_history_bounds_snapshots_and_completed_jobs(db_session: AsyncSession, monkeypatch):
    monkeypatch.setattr(settings, "PAGE_SNAPSHOT_RETENTION_DAYS", 365)
    monkeypatch.setattr(settings, "PAGE_SNAPSHOT_MAX_PER_PAGE", 2)
    monkeypatch.setattr(settings, "REFRESH_JOB_RETENTION_DAYS", 30)
    user = User(username="agency_retention", password_hash=hash_password("AgencyPass12345!"), is_active=True)
    db_session.add(user)
    await db_session.flush()
    page = Page(user_id=user.id, username="retentionpage")
    db_session.add(page)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    db_session.add_all([
        PageSnapshot(page_id=page.id, fetched_at=now - timedelta(days=400)),
        PageSnapshot(page_id=page.id, fetched_at=now - timedelta(days=3)),
        PageSnapshot(page_id=page.id, fetched_at=now - timedelta(days=2)),
        PageSnapshot(page_id=page.id, fetched_at=now - timedelta(days=1)),
    ])
    db_session.add(RefreshJob(
        user_id=user.id,
        status="completed",
        total=1,
        done=1,
        finished_at=now - timedelta(days=31),
    ))
    await db_session.commit()

    await prune_refresh_history(db_session)

    snapshot_count = await db_session.scalar(select(func.count(PageSnapshot.id)).where(PageSnapshot.page_id == page.id))
    job_count = await db_session.scalar(select(func.count(RefreshJob.id)).where(RefreshJob.user_id == user.id))
    assert snapshot_count == 2
    assert job_count == 0
