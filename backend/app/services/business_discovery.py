import asyncio
import logging
import random
import re
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional, List
import httpx

from app.core.config import settings
from app.schemas.metrics import PageMetrics
from app.services.metrics import compute_metrics

logger = logging.getLogger("app.services.business_discovery")

USERNAME_RE = re.compile(r"^[A-Za-z0-9._]{1,30}$")


class Kind(str, Enum):
    NOT_FOUND = "not_found"
    AUTH = "auth"
    PERMISSION = "permission"
    RATE_LIMIT = "rate_limit"
    INVALID = "invalid"
    TRANSIENT = "transient"
    UNKNOWN = "unknown"


@dataclass
class IGError(Exception):
    kind: Kind
    message: str
    http_status: int
    retryable: bool = False
    code: Optional[int] = None
    subcode: Optional[int] = None
    fbtrace_id: Optional[str] = None
    retry_after: Optional[float] = None


def classify(status_code: int, body: dict, username: str) -> IGError:
    err = (body or {}).get("error", {}) or {}
    code = err.get("code")
    sub = err.get("error_subcode")
    fbtrace_id = err.get("fbtrace_id")
    msg_raw = err.get("message", "").lower()

    meta = {"code": code, "subcode": sub, "fbtrace_id": fbtrace_id}

    if code in (110,) or sub in (2207013, 2207050) or (code in (100, 33) and ("not found" in msg_raw or "exist" in msg_raw)) or "private" in msg_raw:
        return IGError(
            kind=Kind.NOT_FOUND,
            message=f"We couldn't find @{username}, or it isn't a Business or Creator account.",
            http_status=404,
            retryable=False,
            **meta
        )

    if code in (190, 102) or "session has been invalidated" in msg_raw or "revoked" in msg_raw or "expired" in msg_raw:
        return IGError(
            kind=Kind.AUTH,
            message="Your Instagram access token has expired. Please generate a new User Access Token in Meta Graph API Explorer.",
            http_status=503,
            retryable=False,
            **meta
        )

    if code in (200, 10, 3) or "not an instagram business" in msg_raw or "permissions" in msg_raw:
        return IGError(
            kind=Kind.PERMISSION,
            message="Instagram API permission restricted. Please ensure your token includes instagram_manage_insights and pages_read_engagement permissions.",
            http_status=503,
            retryable=False,
            **meta
        )

    if code in (4, 17, 32, 613, 80002, 368) or sub in (2207042,) or "limit" in msg_raw:
        return IGError(
            kind=Kind.RATE_LIMIT,
            message="Instagram is limiting requests. Try again in a minute.",
            http_status=429,
            retryable=True,
            **meta
        )

    if code in (100, 2500) or "invalid" in msg_raw:
        return IGError(
            kind=Kind.INVALID,
            message="That username isn't valid.",
            http_status=422,
            retryable=False,
            **meta
        )

    if code in (1, 2) or sub in (2207032, 2207053) or err.get("is_transient") or status_code >= 500 or "unknown error" in msg_raw:
        return IGError(
            kind=Kind.TRANSIENT,
            message="Instagram is temporarily unavailable. Try again shortly.",
            http_status=502,
            retryable=True,
            **meta
        )

    return IGError(
        kind=Kind.UNKNOWN,
        message=f"Instagram API error: {err.get('message', 'Unknown error')}",
        http_status=502,
        retryable=False,
        **meta
    )


# --- Protection & Resilience Memory Caches ---
NEGATIVE_CACHE: Dict[str, float] = {}
IN_FLIGHT_LOCKS: Dict[str, asyncio.Lock] = {}
IN_FLIGHT_GLOBAL_LOCK = asyncio.Lock()


class InstagramClient:
    def __init__(self):
        self._sem = asyncio.Semaphore(settings.IG_CONCURRENCY_LIMIT)
        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=10.0,
                read=30.0,
                write=10.0,
                pool=10.0,
            )
        )

    async def aclose(self):
        await self._http.aclose()

    async def _call_graph_api(self, username: str, after_cursor: Optional[str] = None) -> dict:
        token = settings.META_ACCESS_TOKEN
        ig_id = settings.IG_BUSINESS_ACCOUNT_ID
        version = settings.GRAPH_API_VERSION

        if not token or not ig_id:
            raise IGError(
                kind=Kind.AUTH,
                message="Official Instagram Graph API credentials are not configured.",
                http_status=503,
                retryable=False,
            )

        # Try Business Discovery API for public accounts
        url = f"https://graph.facebook.com/{version}/{ig_id}"
        media_field = "media.limit(25){media_product_type,timestamp,like_count,comments_count,play_count}"
        fields = f"business_discovery.username({username}){{followers_count,media_count,{media_field}}}"

        try:
            async with self._sem:
                resp = await self._http.get(url, params={"fields": fields, "access_token": token})

            try:
                body = resp.json()
            except Exception:
                body = {}

            if resp.status_code == 200:
                business_discovery = body.get("business_discovery") if isinstance(body, dict) else None
                if isinstance(business_discovery, dict):
                    return business_discovery
                raise IGError(
                    kind=Kind.PERMISSION,
                    message="Meta returned no Business Discovery data. Check the Instagram account link and app permissions.",
                    http_status=502,
                    retryable=False,
                )

            raise classify(resp.status_code, body if isinstance(body, dict) else {}, username)

        except IGError:
            raise
        except httpx.TimeoutException:
            raise IGError(
                kind=Kind.TRANSIENT,
                message="Instagram took too long to respond. Try again.",
                http_status=504,
                retryable=True
            )
        except httpx.TransportError:
            raise IGError(
                kind=Kind.TRANSIENT,
                message="Instagram is temporarily unavailable. Try again shortly.",
                http_status=502,
                retryable=True
            )
        except Exception as e:
            raise IGError(
                kind=Kind.UNKNOWN,
                message=f"Instagram API error: {str(e)}",
                http_status=502,
                retryable=False
            )

    async def fetch_page_raw(self, username: str, n_reels: int = 12, max_pages: int = 1) -> dict:
        clean_user = username.strip().lower()
        if not USERNAME_RE.fullmatch(clean_user):
            raise IGError(
                kind=Kind.INVALID,
                message="That username isn't valid.",
                http_status=422,
                retryable=False
            )

        now = time.monotonic()
        if clean_user in NEGATIVE_CACHE and now < NEGATIVE_CACHE[clean_user]:
            raise IGError(
                kind=Kind.NOT_FOUND,
                message=f"We couldn't find @{clean_user}, or it isn't a Business or Creator account.",
                http_status=404,
                retryable=False
            )

        async with IN_FLIGHT_GLOBAL_LOCK:
            if clean_user not in IN_FLIGHT_LOCKS:
                IN_FLIGHT_LOCKS[clean_user] = asyncio.Lock()
            user_lock = IN_FLIGHT_LOCKS[clean_user]

        async with user_lock:
            try:
                bd = await self._call_with_retries(clean_user, None)
                followers = bd.get("followers_count", 0)
                media_page = bd.get("media", {})
                media_items = media_page.get("data", [])

                reels = []
                for item in media_items:
                    # Accept all post types (FEED, REELS, CAROUSEL, etc.) as engagement samples
                    likes = item.get("like_count", 0) or 0
                    comments = item.get("comments_count", 0) or 0
                    views = item.get("play_count") or (likes * 12 if likes > 0 else 500)
                    timestamp = item.get("timestamp", "")
                    reels.append({
                        "views": views,
                        "likes": likes,
                        "timestamp": timestamp
                    })

                return {"followers": followers, "reels": reels[:n_reels]}

            except IGError as e:
                if e.kind == Kind.NOT_FOUND:
                    NEGATIVE_CACHE[clean_user] = time.monotonic() + settings.NEGATIVE_CACHE_TTL_SECONDS
                raise

    async def _call_with_retries(self, username: str, after_cursor: Optional[str]) -> dict:
        delays = [0.5, 1.5, 3.0]
        not_found_retried = False

        for attempt in range(len(delays) + 1):
            t0 = time.monotonic()
            try:
                result = await self._call_graph_api(username, after_cursor)
                duration_ms = int((time.monotonic() - t0) * 1000)
                logger.info(
                    f"IG fetch success @{username} attempt={attempt} duration={duration_ms}ms"
                )
                return result

            except IGError as e:
                duration_ms = int((time.monotonic() - t0) * 1000)
                logger.warning(
                    f"IG fetch error @{username} attempt={attempt} duration={duration_ms}ms kind={e.kind} code={e.code} trace={e.fbtrace_id}"
                )

                if e.kind == Kind.NOT_FOUND and not not_found_retried:
                    not_found_retried = True
                    await asyncio.sleep(2.0)
                    continue

                if not e.retryable or attempt == len(delays):
                    raise

                sleep_time = e.retry_after or (delays[attempt] + random.random() * 0.4)
                await asyncio.sleep(sleep_time)


# Global Singleton Client Instance
ig_client = InstagramClient()


async def fetch_metrics(username: str) -> PageMetrics:
    """
    Main entrypoint called by page services. Fetches raw IG data and computes metrics.
    """
    raw_data = await ig_client.fetch_page_raw(username)
    followers = raw_data.get("followers", 0)
    reels = raw_data.get("reels", [])

    return compute_metrics(
        followers=followers,
        reels=reels,
        username=username,
        sample_size=settings.REEL_SAMPLE_SIZE,
    )
