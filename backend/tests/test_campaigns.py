import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.models import Page, User


async def login(client: AsyncClient, username: str) -> str:
    csrf = (await client.get("/api/v1/auth/csrf")).json()["csrf_token"]
    await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "AgencyPass12345!"},
        headers={"X-CSRF-Token": csrf},
    )
    return csrf


@pytest.mark.asyncio
async def test_page_tags_and_campaign_membership(client: AsyncClient, db_session: AsyncSession):
    user = User(username="campaign_owner", password_hash=hash_password("AgencyPass12345!"), is_active=True)
    db_session.add(user)
    await db_session.flush()
    pages = [Page(user_id=user.id, username=name) for name in ("cricketdaily", "filmreels")]
    db_session.add_all(pages)
    await db_session.commit()
    for page in pages:
        await db_session.refresh(page)
    csrf = await login(client, "campaign_owner")

    tagged = await client.put(
        f"/api/v1/pages/{pages[0].id}/tags",
        json={"tags": ["Cricket", "Meme page", " cricket "]},
        headers={"X-CSRF-Token": csrf},
    )
    assert tagged.status_code == 200
    assert tagged.json()["tags"] == ["Cricket", "Meme page"]

    first = await client.post(
        "/api/v1/campaigns",
        json={"name": "October launch", "page_ids": [str(pages[0].id), str(pages[1].id)]},
        headers={"X-CSRF-Token": csrf},
    )
    second = await client.post(
        "/api/v1/campaigns",
        json={"name": "Cricket collab", "page_ids": [str(pages[0].id)]},
        headers={"X-CSRF-Token": csrf},
    )
    assert first.status_code == second.status_code == 201
    assert set(first.json()["page_ids"]) == {str(page.id) for page in pages}
    assert second.json()["page_ids"] == [str(pages[0].id)]

    listed = await client.get("/api/v1/pages")
    assert next(page for page in listed.json()["items"] if page["id"] == str(pages[0].id))["tags"] == ["Cricket", "Meme page"]

    updated = await client.put(
        f"/api/v1/campaigns/{first.json()['id']}",
        json={"name": "October launch update", "description": "Updated roster", "page_ids": [str(pages[1].id)]},
        headers={"X-CSRF-Token": csrf},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "October launch update"
    assert updated.json()["page_ids"] == [str(pages[1].id)]

    deleted = await client.delete(
        f"/api/v1/campaigns/{second.json()['id']}",
        headers={"X-CSRF-Token": csrf},
    )
    assert deleted.status_code == 200
    assert len((await client.get("/api/v1/pages")).json()["items"]) == 2


@pytest.mark.asyncio
async def test_campaign_rejects_pages_owned_by_another_user(client: AsyncClient, db_session: AsyncSession):
    owner = User(username="campaign_owner_b", password_hash=hash_password("AgencyPass12345!"), is_active=True)
    other = User(username="campaign_other", password_hash=hash_password("AgencyPass12345!"), is_active=True)
    db_session.add_all([owner, other])
    await db_session.flush()
    other_page = Page(user_id=other.id, username="privatepage")
    db_session.add(other_page)
    await db_session.commit()
    csrf = await login(client, "campaign_owner_b")

    response = await client.post(
        "/api/v1/campaigns",
        json={"name": "Invalid membership", "page_ids": [str(other_page.id)]},
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 404