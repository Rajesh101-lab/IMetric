import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Page, PageSnapshot, PageTag, User
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
    assert len(list_a.json()["items"]) == 1
    assert list_a.json()["items"][0]["username"] == "nike"

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
    assert len(list_b.json()["items"]) == 0

    # Agency B adds page 'adidas'
    add_b = await client.post(
        "/api/v1/pages",
        json={"username": "adidas"},
        headers={"X-CSRF-Token": csrf_token}
    )
    assert add_b.status_code in (201, 202)

    list_b2 = await client.get("/api/v1/pages")
    assert len(list_b2.json()["items"]) == 1
    assert list_b2.json()["items"][0]["username"] == "adidas"


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
    pages = res_desc.json()["items"]
    assert len(pages) == 2

    # Invalid sort field should fallback safely without error
    res_inv = await client.get("/api/v1/pages?sort=invalid_column&order=asc")
    assert res_inv.status_code == 200


@pytest.mark.asyncio
async def test_page_pagination_search_and_workspace_summary(client: AsyncClient, db_session: AsyncSession):
    user = User(username="agency_paging", password_hash=hash_password("AgencyPass12345!"), is_active=True)
    db_session.add(user)
    await db_session.flush()
    pages = [
        Page(user_id=user.id, username=f"creator{number}", followers=number * 10, avg_views_per_follower=0.1)
        for number in range(1, 6)
    ]
    db_session.add_all(pages)
    await db_session.flush()
    db_session.add(PageTag(page_id=pages[3].id, label="Cricket"))
    await db_session.commit()

    csrf_token = (await client.get("/api/v1/auth/csrf")).json()["csrf_token"]
    await client.post(
        "/api/v1/auth/login",
        json={"username": "agency_paging", "password": "AgencyPass12345!"},
        headers={"X-CSRF-Token": csrf_token},
    )

    first_page = await client.get("/api/v1/pages?page=1&page_size=2&sort=username&order=asc")
    second_page = await client.get("/api/v1/pages?page=2&page_size=2&sort=username&order=asc")
    assert first_page.status_code == second_page.status_code == 200
    assert [page["username"] for page in first_page.json()["items"]] == ["creator1", "creator2"]
    assert [page["username"] for page in second_page.json()["items"]] == ["creator3", "creator4"]
    assert first_page.json()["total"] == 5
    assert first_page.json()["total_pages"] == 3
    assert first_page.json()["summary"] == {
        "total_pages": 5,
        "total_followers": 150,
        "avg_views_per_follower": 0.1,
    }

    search = await client.get("/api/v1/pages?q=cricket")
    assert search.status_code == 200
    assert [page["username"] for page in search.json()["items"]] == ["creator4"]
    assert search.json()["total"] == 1
    assert search.json()["summary"]["total_pages"] == 5

    invalid_page_size = await client.get("/api/v1/pages?page_size=201")
    assert invalid_page_size.status_code == 422


@pytest.mark.asyncio
async def test_delete_page_removes_owned_page_only(client: AsyncClient, db_session: AsyncSession):
    user, other_user = await setup_two_agencies(db_session)
    owned_page = Page(user_id=user.id, username="nike")
    other_page = Page(user_id=other_user.id, username="adidas")
    db_session.add_all([owned_page, other_page])
    await db_session.commit()
    await db_session.refresh(owned_page)

    csrf_res = await client.get("/api/v1/auth/csrf")
    csrf_token = csrf_res.json()["csrf_token"]
    await client.post(
        "/api/v1/auth/login",
        json={"username": "agency_a", "password": "AgencyPass12345!"},
        headers={"X-CSRF-Token": csrf_token}
    )

    delete_res = await client.delete(
        f"/api/v1/pages/{owned_page.id}",
        headers={"X-CSRF-Token": csrf_token}
    )
    assert delete_res.status_code == 200
    assert delete_res.json() == {"message": "Page removed successfully."}

    list_res = await client.get("/api/v1/pages")
    assert [page["username"] for page in list_res.json()["items"]] == []

    other_page_res = await client.delete(
        f"/api/v1/pages/{other_page.id}",
        headers={"X-CSRF-Token": csrf_token}
    )
    assert other_page_res.status_code == 404


@pytest.mark.asyncio
async def test_delete_page_with_snapshots(client: AsyncClient, db_session: AsyncSession):
    user, _ = await setup_two_agencies(db_session)
    page = Page(user_id=user.id, username="nike", followers=1000)
    db_session.add(page)
    await db_session.commit()
    await db_session.refresh(page)

    snapshot = PageSnapshot(page_id=page.id, followers=1000, reels_sampled=3)
    db_session.add(snapshot)
    await db_session.commit()

    csrf_res = await client.get("/api/v1/auth/csrf")
    csrf_token = csrf_res.json()["csrf_token"]
    await client.post(
        "/api/v1/auth/login",
        json={"username": "agency_a", "password": "AgencyPass12345!"},
        headers={"X-CSRF-Token": csrf_token}
    )

    delete_res = await client.delete(
        f"/api/v1/pages/{page.id}",
        headers={"X-CSRF-Token": csrf_token}
    )
    assert delete_res.status_code == 200

    list_res = await client.get("/api/v1/pages")
    assert list_res.json()["items"] == []
