import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Tuple, Optional, Dict, Any
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.core.security import normalize_username, validate_username_format
from app.db.models import Page, PageSnapshot
from app.db.session import AsyncSessionLocal
from app.services.business_discovery import IGError, Kind
from app.services.metrics import compute_metrics
from app.services.providers.chain import provider_chain

REFRESH_ALL_JOBS: Dict[UUID, Dict[str, Any]] = {}
REFRESH_ALL_LOCK = asyncio.Lock()

ALLOWED_SORT_FIELDS = {
    "username": Page.username,
    "followers": Page.followers,
    "last_reel_likes": Page.last_reel_likes,
    "last_reel_views": Page.last_reel_views,
    "avg_views": Page.avg_views,
    "median_views": Page.median_views,
    "avg_likes": Page.avg_likes,
    "like_to_view_ratio": Page.like_to_view_ratio,
    "avg_views_per_follower": Page.avg_views_per_follower,
    "last_refreshed_at": Page.last_refreshed_at,
    "created_at": Page.created_at,
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


async def recover_stuck_pending_pages():
    """
    On app startup, marks any pending pages older than 2 minutes as failed (Kind.TRANSIENT).
    """
    cutoff = utc_now() - timedelta(minutes=2)
    async with AsyncSessionLocal() as session:
        stmt = (
            update(Page)
            .where(Page.status == "pending", Page.updated_at <= cutoff)
            .values(
                status="failed",
                error_kind=Kind.TRANSIENT.value,
                error_message="Instagram took too long to respond. Try again."
            )
        )
        await session.execute(stmt)
        await session.commit()
        logger.info("Recovered stuck pending page rows on startup.")


async def list_user_pages(
    db: AsyncSession,
    user_id: UUID,
    sort_by: str = "followers",
    order: str = "desc"
) -> List[Page]:
    sort_col = ALLOWED_SORT_FIELDS.get(sort_by.lower(), Page.followers)
    is_desc = (order.lower() == "desc")

    if is_desc:
        ordering = sort_col.desc().nulls_last()
    else:
        ordering = sort_col.asc().nulls_last()

    stmt = select(Page).where(Page.user_id == user_id).order_by(ordering)
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def add_or_upsert_page(
    db: AsyncSession,
    user_id: UUID,
    raw_username: str
) -> Tuple[Page, bool]:
    clean_username = normalize_username(raw_username)
    if not validate_username_format(clean_username):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "INVALID", "message": "That username isn't valid."}
        )

    stmt = select(Page).where(Page.user_id == user_id, Page.username == clean_username)
    res = await db.execute(stmt)
    page = res.scalar_one_or_none()

    if page:
        page.status = "pending"
        page.error_kind = None
        page.error_message = None
        created = False
    else:
        page = Page(
            user_id=user_id,
            username=clean_username,
            status="pending",
            source="official",
            fallback_reason=None,
            error_kind=None,
            error_message=None,
        )
        db.add(page)
        created = True

    await db.commit()
    await db.refresh(page)

    # Launch background fetch task
    asyncio.create_task(_run_add_page_fetch_task(page.id, user_id, clean_username))
    return page, created


async def _run_add_page_fetch_task(page_id: UUID, user_id: UUID, username: str):
    async with AsyncSessionLocal() as session:
        try:
            raw_data = await provider_chain.fetch(username, agency_id=user_id, n_reels=settings.REEL_SAMPLE_SIZE)

            stmt = select(Page).where(Page.id == page_id, Page.user_id == user_id)
            res = await session.execute(stmt)
            page = res.scalar_one_or_none()

            if page:
                # Data Quality Guard Check
                if (
                    page.status == "ready"
                    and page.followers > 0
                    and raw_data.source == "backup"
                ):
                    follower_diff = abs(raw_data.followers - page.followers) / page.followers
                    if follower_diff > 0.5 or (len(raw_data.reels) == 0 and page.reels_sampled > 0):
                        logger.warning(
                            f"Data quality guard rejected backup result for @{username}: follower_diff={follower_diff:.2f}, reels_count={len(raw_data.reels)}"
                        )
                        page.status = "failed"
                        page.error_kind = Kind.TRANSIENT.value
                        page.error_message = "Instagram is temporarily unavailable. Try again shortly."
                        page.last_refresh_error = "Instagram is temporarily unavailable. Try again shortly."
                        await session.commit()
                        return

                metrics = compute_metrics(
                    followers=raw_data.followers,
                    reels=raw_data.reels,
                    username=username,
                    sample_size=settings.REEL_SAMPLE_SIZE,
                )

                page.status = "ready"
                page.source = raw_data.source
                page.fallback_reason = raw_data.fallback_reason
                page.error_kind = None
                page.error_message = None
                page.followers = metrics.followers
                page.last_reel_likes = metrics.lastreellikes
                page.last_reel_views = metrics.lastreelviews
                page.avg_views = metrics.avgviews
                page.median_views = metrics.medianviews
                page.avg_likes = metrics.avglikes
                page.like_to_view_ratio = metrics.liketoviewratio
                page.avg_views_per_follower = metrics.avgviewsperfollower
                page.reels_sampled = metrics.reelssampled
                page.last_refreshed_at = metrics.fetched_at

                snapshot = PageSnapshot(
                    page_id=page.id,
                    source=raw_data.source,
                    fallback_reason=raw_data.fallback_reason,
                    followers=metrics.followers,
                    last_reel_likes=metrics.lastreellikes,
                    last_reel_views=metrics.lastreelviews,
                    avg_views=metrics.avgviews,
                    median_views=metrics.medianviews,
                    avg_likes=metrics.avglikes,
                    like_to_view_ratio=metrics.liketoviewratio,
                    avg_views_per_follower=metrics.avgviewsperfollower,
                    reels_sampled=metrics.reelssampled,
                    fetched_at=metrics.fetched_at,
                )
                session.add(snapshot)
                await session.commit()

        except IGError as exc:
            logger.warning(f"Background fetch task failed for @{username}: kind={exc.kind} msg={exc.message}")
            stmt = select(Page).where(Page.id == page_id, Page.user_id == user_id)
            res = await session.execute(stmt)
            page = res.scalar_one_or_none()
            if page:
                page.status = "failed"
                page.error_kind = exc.kind.value
                page.error_message = exc.message
                page.last_refresh_error = exc.message
                await session.commit()

        except Exception as exc:
            logger.error(f"Unexpected error in background fetch for @{username}: {exc}")
            stmt = select(Page).where(Page.id == page_id, Page.user_id == user_id)
            res = await session.execute(stmt)
            page = res.scalar_one_or_none()
            if page:
                page.status = "failed"
                page.error_kind = Kind.UNKNOWN.value
                page.error_message = "Something went wrong talking to Instagram. Try again."
                page.last_refresh_error = "Something went wrong talking to Instagram. Try again."
                await session.commit()


async def refresh_single_page(
    db: AsyncSession,
    user_id: UUID,
    page_id: UUID
) -> Page:
    stmt = select(Page).where(Page.id == page_id, Page.user_id == user_id)
    res = await db.execute(stmt)
    page = res.scalar_one_or_none()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PAGE_NOT_FOUND", "message": "Page not found or does not belong to your agency."}
        )

    now = utc_now()
    last_ref = ensure_utc(page.last_refreshed_at)
    if last_ref:
        elapsed = (now - last_ref).total_seconds()
        if elapsed < 60:
            remaining = int(60 - elapsed)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"code": "COOLDOWN", "message": f"Please wait a moment before refreshing again. Try again in {remaining}s."}
            )

    try:
        raw_data = await provider_chain.fetch(page.username, agency_id=user_id, n_reels=settings.REEL_SAMPLE_SIZE)

        # Data Quality Guard
        if (
            page.status == "ready"
            and page.followers > 0
            and raw_data.source == "backup"
        ):
            follower_diff = abs(raw_data.followers - page.followers) / page.followers
            if follower_diff > 0.5 or (len(raw_data.reels) == 0 and page.reels_sampled > 0):
                logger.warning(
                    f"Data quality guard rejected backup result on refresh for @{page.username}: follower_diff={follower_diff:.2f}"
                )
                page.error_kind = Kind.TRANSIENT.value
                page.error_message = "Instagram is temporarily unavailable. Try again shortly."
                page.last_refresh_error = "Instagram is temporarily unavailable. Try again shortly."
                await db.commit()
                await db.refresh(page)
                return page

        metrics = compute_metrics(
            followers=raw_data.followers,
            reels=raw_data.reels,
            username=page.username,
            sample_size=settings.REEL_SAMPLE_SIZE,
        )

        page.status = "ready"
        page.source = raw_data.source
        page.fallback_reason = raw_data.fallback_reason
        page.error_kind = None
        page.error_message = None
        page.followers = metrics.followers
        page.last_reel_likes = metrics.lastreellikes
        page.last_reel_views = metrics.lastreelviews
        page.avg_views = metrics.avgviews
        page.median_views = metrics.medianviews
        page.avg_likes = metrics.avglikes
        page.like_to_view_ratio = metrics.liketoviewratio
        page.avg_views_per_follower = metrics.avgviewsperfollower
        page.reels_sampled = metrics.reelssampled
        page.last_refreshed_at = metrics.fetched_at
        page.last_refresh_error = None

        snapshot = PageSnapshot(
            page_id=page.id,
            source=raw_data.source,
            fallback_reason=raw_data.fallback_reason,
            followers=metrics.followers,
            last_reel_likes=metrics.lastreellikes,
            last_reel_views=metrics.lastreelviews,
            avg_views=metrics.avgviews,
            median_views=metrics.medianviews,
            avg_likes=metrics.avglikes,
            like_to_view_ratio=metrics.liketoviewratio,
            avg_views_per_follower=metrics.avgviewsperfollower,
            reels_sampled=metrics.reelssampled,
            fetched_at=metrics.fetched_at,
        )
        db.add(snapshot)
        await db.commit()
        await db.refresh(page)
        return page

    except IGError as exc:
        page.status = "failed" if page.followers == 0 else "ready"
        page.error_kind = exc.kind.value
        page.error_message = exc.message
        page.last_refresh_error = exc.message
        await db.commit()
        await db.refresh(page)
        return page
    except Exception as exc:
        logger.error(f"Error refreshing page {page.username}: {str(exc)}")
        page.error_kind = Kind.UNKNOWN.value
        page.error_message = "Something went wrong talking to Instagram. Try again."
        page.last_refresh_error = "Something went wrong talking to Instagram. Try again."
        await db.commit()
        await db.refresh(page)
        return page


async def start_refresh_all_job(db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
    async with REFRESH_ALL_LOCK:
        existing = REFRESH_ALL_JOBS.get(user_id)
        if existing and existing.get("status") == "running":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "JOB_IN_PROGRESS", "message": "A refresh-all job is already running for your agency."}
            )

        stmt = select(Page.id).where(Page.user_id == user_id)
        res = await db.execute(stmt)
        page_ids = list(res.scalars().all())

        job_id = str(uuid.uuid4())
        job_info = {
            "job_id": job_id,
            "total": len(page_ids),
            "done": 0,
            "failed": 0,
            "status": "running"
        }
        REFRESH_ALL_JOBS[user_id] = job_info

        asyncio.create_task(_run_refresh_all_worker(user_id, job_id, page_ids))
        return job_info


async def _run_refresh_all_worker(user_id: UUID, job_id: str, page_ids: List[UUID]) -> None:
    sem = asyncio.Semaphore(settings.REFRESH_ALL_CONCURRENCY)

    async def _refresh_one(pid: UUID):
        async with sem:
            async with AsyncSessionLocal() as session:
                try:
                    stmt = select(Page).where(Page.id == pid, Page.user_id == user_id)
                    res = await session.execute(stmt)
                    p = res.scalar_one_or_none()
                    if not p:
                        return False

                    raw_data = await provider_chain.fetch(p.username, agency_id=user_id, n_reels=settings.REEL_SAMPLE_SIZE)
                    metrics = compute_metrics(
                        followers=raw_data.followers,
                        reels=raw_data.reels,
                        username=p.username,
                        sample_size=settings.REEL_SAMPLE_SIZE,
                    )
                    p.status = "ready"
                    p.source = raw_data.source
                    p.fallback_reason = raw_data.fallback_reason
                    p.error_kind = None
                    p.error_message = None
                    p.followers = metrics.followers
                    p.last_reel_likes = metrics.lastreellikes
                    p.last_reel_views = metrics.lastreelviews
                    p.avg_views = metrics.avgviews
                    p.median_views = metrics.medianviews
                    p.avg_likes = metrics.avglikes
                    p.like_to_view_ratio = metrics.liketoviewratio
                    p.avg_views_per_follower = metrics.avgviewsperfollower
                    p.reels_sampled = metrics.reelssampled
                    p.last_refreshed_at = metrics.fetched_at
                    p.last_refresh_error = None

                    snapshot = PageSnapshot(
                        page_id=p.id,
                        source=raw_data.source,
                        fallback_reason=raw_data.fallback_reason,
                        followers=metrics.followers,
                        last_reel_likes=metrics.lastreellikes,
                        last_reel_views=metrics.lastreelviews,
                        avg_views=metrics.avgviews,
                        median_views=metrics.medianviews,
                        avg_likes=metrics.avglikes,
                        like_to_view_ratio=metrics.liketoviewratio,
                        avg_views_per_follower=metrics.avgviewsperfollower,
                        reels_sampled=metrics.reelssampled,
                        fetched_at=metrics.fetched_at,
                    )
                    session.add(snapshot)
                    await session.commit()
                    return True
                except Exception as exc:
                    logger.warning(f"Refresh-all error for page {pid}: {str(exc)}")
                    try:
                        stmt = select(Page).where(Page.id == pid, Page.user_id == user_id)
                        res = await session.execute(stmt)
                        p = res.scalar_one_or_none()
                        if p:
                            p.last_refresh_error = "Refresh failed."
                            await session.commit()
                    except Exception:
                        pass
                    return False

    tasks = [_refresh_one(pid) for pid in page_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    done_count = sum(1 for r in results if r is True)
    failed_count = sum(1 for r in results if r is False or isinstance(r, Exception))

    async with REFRESH_ALL_LOCK:
        job = REFRESH_ALL_JOBS.get(user_id)
        if job and job.get("job_id") == job_id:
            job["done"] = done_count
            job["failed"] = failed_count
            job["status"] = "completed"


def get_refresh_all_job_status(user_id: UUID, job_id: str) -> Dict[str, Any]:
    job = REFRESH_ALL_JOBS.get(user_id)
    if not job or job.get("job_id") != job_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_NOT_FOUND", "message": "Refresh-all job not found."}
        )
    return job
