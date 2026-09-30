import logging
import pytest
from app.core.config import settings
from app.services.business_discovery import IGError, Kind
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
