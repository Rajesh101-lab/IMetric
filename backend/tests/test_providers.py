import logging
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.core.config import settings
from app.db.models import Base, ProviderUsage, User
from app.services.business_discovery import IGError, InstagramClient, Kind
from app.services.providers import chain as provider_chain_module
from app.services.providers.chain import ProviderChain, ProviderUsageTracker
from app.services.providers.serpapi import SerpApiProvider, APIKeyRedactorFilter


def test_api_key_redaction_in_logs():
    filter_obj = APIKeyRedactorFilter(api_key="secret_serpapi_key_12345")
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Calling https://serpapi.com/search.json?api_key=secret_serpapi_key_12345 for profile",
        args=(),
        exc_info=None
    )
    filter_obj.filter(record)
    assert "secret_serpapi_key_12345" not in record.msg
    assert "[REDACTED_API_KEY]" in record.msg


@pytest.mark.asyncio
async def test_serpapi_mock_fallback_when_unconfigured():
    provider = SerpApiProvider()
    data = await provider.fetch("mockbrand", n_reels=12)
    assert data.source == "backup"
    assert data.followers > 0
    assert len(data.reels) > 0


class _FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_serpapi_parses_profile_results(monkeypatch):
    monkeypatch.setattr(settings, "SERPAPI_API_KEY", "test-key")
    provider = SerpApiProvider()
    payload = {
        "profile_results": {
            "followers": 334,
            "is_private": False,
            "username": "serpapicom",
            "posts": [
                {
                    "is_video": False,
                    "product_type": "feed",
                    "liked_by_count": 20,
                    "timestamp": "2026-09-30T12:00:00Z",
                },
                {
                    "is_video": True,
                    "product_type": "clips",
                    "liked_by_count": 40,
                    "video_view_count": 1200,
                    "timestamp": "2026-09-29T12:00:00Z",
                },
            ],
        }
    }
    provider._http.get = AsyncMock(return_value=_FakeResponse(payload))

    data = await provider.fetch("serpapicom", n_reels=12)

    assert data.source == "backup"
    assert data.followers == 334
    assert len(data.reels) == 1
    assert data.reels[0]["likes"] == 40
    assert data.reels[0]["views"] == 1200


def test_backup_normalization_skips_video_without_views():
    provider = SerpApiProvider()

    normalized = provider._normalize_post({
        "is_video": True,
        "product_type": "clips",
        "liked_by_count": 40,
    })

    assert normalized is None


@pytest.mark.asyncio
async def test_official_provider_requires_graph_api_credentials(monkeypatch):
    monkeypatch.setattr(settings, "META_ACCESS_TOKEN", "")
    monkeypatch.setattr(settings, "IG_BUSINESS_ACCOUNT_ID", "")
    client = InstagramClient()

    with pytest.raises(IGError) as error:
        await client._call_graph_api("samplebrand")

    assert error.value.kind == Kind.AUTH
    assert "credentials are not configured" in error.value.message
    await client.aclose()


@pytest.mark.asyncio
async def test_business_discovery_error_does_not_query_connected_account(monkeypatch):
    monkeypatch.setattr(settings, "META_ACCESS_TOKEN", "test-token")
    monkeypatch.setattr(settings, "IG_BUSINESS_ACCOUNT_ID", "test-account")
    client = InstagramClient()
    client._http.get = AsyncMock(return_value=_FakeResponse({
        "error": {"message": "Invalid OAuth access token", "code": 190}
    }, status_code=400))

    with pytest.raises(IGError) as error:
        await client._call_graph_api("samplebrand")

    assert error.value.kind == Kind.AUTH
    client._http.get.assert_awaited_once()
    await client.aclose()


@pytest.mark.asyncio
async def test_provider_chain_does_not_call_backup_when_disabled(monkeypatch):
    monkeypatch.setattr(settings, "BACKUP_ENABLED", False)
    chain = ProviderChain()
    chain.primary = SimpleNamespace(fetch_page_raw=AsyncMock(side_effect=IGError(
        kind=Kind.PERMISSION,
        message="Meta permission denied.",
        http_status=403,
    )))
    chain.backup = SimpleNamespace(
        is_circuit_open=False,
        fetch=AsyncMock(),
    )

    with pytest.raises(IGError) as error:
        await chain.fetch("samplebrand", agency_id=uuid4())

    assert error.value.kind == Kind.PERMISSION
    chain.backup.fetch.assert_not_awaited()


@pytest.mark.asyncio
async def test_provider_chain_does_not_mask_meta_auth_errors(monkeypatch):
    monkeypatch.setattr(settings, "BACKUP_ENABLED", True)
    monkeypatch.setattr(settings, "BACKUP_FALLBACK_ON", "transient,rate_limit")
    chain = ProviderChain()
    chain.primary = SimpleNamespace(fetch_page_raw=AsyncMock(side_effect=IGError(
        kind=Kind.AUTH,
        message="Meta access token expired.",
        http_status=503,
    )))
    chain.backup = SimpleNamespace(
        is_circuit_open=False,
        fetch=AsyncMock(),
    )

    with pytest.raises(IGError) as error:
        await chain.fetch("samplebrand", agency_id=uuid4())

    assert error.value.kind == Kind.AUTH
    chain.backup.fetch.assert_not_awaited()


@pytest.mark.asyncio
async def test_backup_quota_reservation_is_atomic_and_fails_closed(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(provider_chain_module, "AsyncSessionLocal", session_factory)
    monkeypatch.setattr(settings, "BACKUP_PER_AGENCY_DAILY_LIMIT", 2)
    monkeypatch.setattr(settings, "BACKUP_DAILY_LIMIT", 3)

    async with session_factory() as session:
        agency_a = User(username="quota_agency_a", password_hash="test", is_active=True)
        agency_b = User(username="quota_agency_b", password_hash="test", is_active=True)
        session.add_all([agency_a, agency_b])
        await session.commit()
        agency_a_id = agency_a.id
        agency_b_id = agency_b.id

    assert await ProviderUsageTracker.reserve_call(agency_a_id, "serpapi") is True
    await ProviderUsageTracker.record_failure(agency_a_id, "serpapi")
    assert await ProviderUsageTracker.reserve_call(agency_a_id, "serpapi") is True
    assert await ProviderUsageTracker.reserve_call(agency_a_id, "serpapi") is False
    assert await ProviderUsageTracker.reserve_call(agency_b_id, "serpapi") is True
    assert await ProviderUsageTracker.reserve_call(agency_b_id, "serpapi") is False

    async with session_factory() as session:
        usages = (await session.execute(select(ProviderUsage))).scalars().all()
        assert sum(usage.calls for usage in usages) == 3
        assert sum(usage.failures for usage in usages) == 1
    await engine.dispose()
