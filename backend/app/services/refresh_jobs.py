import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, or_, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Page, PageSnapshot, RefreshJob, RefreshJobItem, User
from app.db.session import AsyncSessionLocal
from app.services.metrics import compute_metrics
from app.services.providers.chain import provider_chain

logger = logging.getLogger("app.services.refresh_jobs")
GLOBAL_REFRESH_LOCK_ID = 0x52454652455348


def _job_response(job: RefreshJob) -> Dict[str, Any]:
    return {
        "job_id": str(job.id),
        "total": job.total,
        "done": job.done,
        "failed": job.failed,
        "status": job.status,
    }


async def _enqueue_pages(
    db: AsyncSession,
    user_id: UUID,
    page_ids: Optional[List[UUID]],
    reject_if_active: bool,
) -> Dict[str, Any]:
    await db.execute(select(User.id).where(User.id == user_id).with_for_update())
    if page_ids is None:
        result = await db.execute(select(Page.id).where(Page.user_id == user_id).order_by(Page.id))
        requested_ids = list(result.scalars().all())
    else:
        requested_ids = list(dict.fromkeys(page_ids))

    active_result = await db.execute(
        select(RefreshJob)
        .where(
            RefreshJob.user_id == user_id,
            RefreshJob.status.in_(("queued", "running")),
        )
        .order_by(RefreshJob.created_at.desc())
        .limit(1)
        .with_for_update()
    )
    job = active_result.scalar_one_or_none()
    if job and reject_if_active and job.is_refresh_all:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "JOB_IN_PROGRESS", "message": "A refresh-all job is already queued or running for your agency."},
        )

    if job:
        if reject_if_active:
            job.is_refresh_all = True
        active_item_result = await db.execute(
            select(RefreshJobItem.page_id).where(
                RefreshJobItem.job_id == job.id,
                RefreshJobItem.status.in_(("queued", "running")),
                RefreshJobItem.page_id.in_(requested_ids) if requested_ids else text("1 = 0"),
            )
        )
        already_active = set(active_item_result.scalars().all())
        missing_ids = [page_id for page_id in requested_ids if page_id not in already_active]
        if missing_ids:
            db.add_all([RefreshJobItem(job_id=job.id, page_id=page_id) for page_id in missing_ids])
            job.total += len(missing_ids)
    else:
        job = RefreshJob(
            user_id=user_id,
            status="queued",
            is_refresh_all=reject_if_active,
            total=len(requested_ids),
            done=0,
            failed=0,
        )
        db.add(job)
        await db.flush()
        if requested_ids:
            db.add_all([RefreshJobItem(job_id=job.id, page_id=page_id) for page_id in requested_ids])
        else:
            job.status = "completed"
            job.finished_at = datetime.now(timezone.utc)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "JOB_IN_PROGRESS", "message": "A refresh-all job is already queued or running for your agency."},
        )
    await db.refresh(job)
    return _job_response(job)


async def create_refresh_job(db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
    return await _enqueue_pages(db, user_id, None, reject_if_active=True)


async def enqueue_page_refresh(db: AsyncSession, user_id: UUID, page_id: UUID) -> Dict[str, Any]:
    return await _enqueue_pages(db, user_id, [page_id], reject_if_active=False)


async def get_refresh_job(db: AsyncSession, user_id: UUID, job_id: str) -> Dict[str, Any]:
    try:
        parsed_id = UUID(job_id)
    except ValueError:
        parsed_id = None
    result = await db.execute(
        select(RefreshJob).where(RefreshJob.id == parsed_id, RefreshJob.user_id == user_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_NOT_FOUND", "message": "Refresh-all job not found."},
        )
    return _job_response(job)


async def get_active_refresh_job(db: AsyncSession, user_id: UUID) -> Optional[Dict[str, Any]]:
    result = await db.execute(
        select(RefreshJob)
        .where(
            RefreshJob.user_id == user_id,
            RefreshJob.is_refresh_all.is_(True),
            RefreshJob.status.in_(("queued", "running")),
        )
        .order_by(RefreshJob.created_at.desc())
        .limit(1)
    )
    job = result.scalar_one_or_none()
    return _job_response(job) if job else None


async def _claim_items(limit: int) -> List[Dict[str, UUID]]:
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        async with session.begin():
            dialect = session.bind.dialect.name if session.bind is not None else ""
            if dialect == "postgresql":
                await session.execute(text("SELECT pg_advisory_xact_lock(:lock_id)"), {"lock_id": GLOBAL_REFRESH_LOCK_ID})
                active_result = await session.execute(
                    select(func.count(RefreshJobItem.id)).where(
                        RefreshJobItem.status == "running",
                        RefreshJobItem.lease_expires_at > now,
                    )
                )
                limit = min(limit, max(0, settings.REFRESH_ALL_CONCURRENCY - int(active_result.scalar_one())))
            if limit <= 0:
                return []

            statement = (
                select(RefreshJobItem)
                .join(RefreshJob, RefreshJob.id == RefreshJobItem.job_id)
                .where(
                    RefreshJob.status.in_(("queued", "running")),
                    or_(
                        RefreshJobItem.status == "queued",
                        (RefreshJobItem.status == "running") & (RefreshJobItem.lease_expires_at <= now),
                    ),
                )
                .order_by(RefreshJobItem.created_at, RefreshJobItem.id)
                .limit(limit)
            )
            if dialect == "postgresql":
                statement = statement.with_for_update(skip_locked=True)
            result = await session.execute(statement)
            items = list(result.scalars().all())
            claims: List[Dict[str, UUID]] = []
            for item in items:
                token = uuid.uuid4()
                item.status = "running"
                item.lease_token = token
                item.lease_expires_at = now + timedelta(seconds=settings.REFRESH_JOB_LEASE_SECONDS)
                item.error = None
                job = await session.get(RefreshJob, item.job_id)
                if job is not None:
                    job.status = "running"
                    job.started_at = job.started_at or now
                claims.append({"item_id": item.id, "job_id": item.job_id, "page_id": item.page_id, "lease_token": token})
            return claims


async def _renew_lease(item_id: UUID, lease_token: UUID) -> None:
    while True:
        await asyncio.sleep(settings.REFRESH_JOB_LEASE_SECONDS / 3)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                update(RefreshJobItem)
                .where(
                    RefreshJobItem.id == item_id,
                    RefreshJobItem.status == "running",
                    RefreshJobItem.lease_token == lease_token,
                )
                .values(lease_expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.REFRESH_JOB_LEASE_SECONDS))
            )
            await session.commit()
            if result.rowcount != 1:
                return


async def _finish_item(
    claim: Dict[str, UUID],
    metrics: Optional[Any],
    source: Optional[str],
    fallback_reason: Optional[str],
    error: Optional[str],
) -> None:
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        async with session.begin():
            item_result = await session.execute(
                select(RefreshJobItem).where(
                    RefreshJobItem.id == claim["item_id"],
                    RefreshJobItem.status == "running",
                    RefreshJobItem.lease_token == claim["lease_token"],
                ).with_for_update()
            )
            item = item_result.scalar_one_or_none()
            if item is None:
                return

            job_result = await session.execute(
                select(RefreshJob).where(RefreshJob.id == claim["job_id"]).with_for_update()
            )
            job = job_result.scalar_one_or_none()
            if job is None:
                return

            page_result = await session.execute(
                select(Page).where(Page.id == claim["page_id"], Page.user_id == job.user_id)
            )
            page = page_result.scalar_one_or_none()
            succeeded = metrics is not None and page is not None
            if succeeded:
                page.status = "ready"
                page.source = source or "official"
                page.fallback_reason = fallback_reason
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
                session.add(PageSnapshot(
                    page_id=page.id,
                    source=source or "official",
                    fallback_reason=fallback_reason,
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
                ))
                item.status = "completed"
                item.error = None
                job.done += 1
            else:
                message = error or "Page no longer belongs to this workspace."
                item.status = "failed"
                item.error = message[:255]
                if page is not None:
                    page.last_refresh_error = "Refresh failed."
                    page.error_message = "Refresh failed."
                job.failed += 1

            item.lease_token = None
            item.lease_expires_at = None
            item.updated_at = now
            if job.done + job.failed >= job.total:
                job.status = "completed"
                job.finished_at = now


async def _process_claim(claim: Dict[str, UUID]) -> None:
    renew_task = asyncio.create_task(_renew_lease(claim["item_id"], claim["lease_token"]))
    metrics = None
    source = None
    fallback_reason = None
    error_message = None
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Page.username, Page.user_id).where(Page.id == claim["page_id"])
            )
            page_data = result.one_or_none()
        if page_data is None:
            error_message = "Page was removed before refresh."
        else:
            username, user_id = page_data
            raw_data = await provider_chain.fetch(
                username,
                agency_id=user_id,
                n_reels=settings.REEL_SAMPLE_SIZE,
            )
            metrics = compute_metrics(
                followers=raw_data.followers,
                reels=raw_data.reels,
                username=username,
                sample_size=settings.REEL_SAMPLE_SIZE,
            )
            source = raw_data.source
            fallback_reason = raw_data.fallback_reason
    except Exception as exc:
        error_message = str(exc) or "Refresh failed."
        logger.exception("Durable refresh item failed", extra={"item_id": str(claim["item_id"])})
    finally:
        renew_task.cancel()
        try:
            await renew_task
        except asyncio.CancelledError:
            pass
    try:
        await _finish_item(claim, metrics, source, fallback_reason, error_message)
    except Exception:
        logger.exception("Could not persist refresh item outcome", extra={"item_id": str(claim["item_id"])})


async def refresh_worker(stop_event: asyncio.Event) -> None:
    logger.info("Durable refresh worker started")
    last_maintenance_day = None
    while not stop_event.is_set():
        try:
            claims = await _claim_items(settings.REFRESH_ALL_CONCURRENCY)
            if claims:
                await asyncio.gather(*(_process_claim(claim) for claim in claims))
                continue
            now = datetime.now(timezone.utc)
            if now.hour >= 3 and last_maintenance_day != now.date():
                async with AsyncSessionLocal() as session:
                    await prune_refresh_history(session)
                last_maintenance_day = now.date()
        except Exception:
            logger.exception("Durable refresh worker iteration failed")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=settings.REFRESH_WORKER_POLL_SECONDS)
        except asyncio.TimeoutError:
            pass
    logger.info("Durable refresh worker stopped")


async def prune_refresh_history(db: AsyncSession, retention_days: Optional[int] = None) -> None:
    retention_days = retention_days or settings.REFRESH_JOB_RETENTION_DAYS
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    snapshot_cutoff = datetime.now(timezone.utc) - timedelta(days=settings.PAGE_SNAPSHOT_RETENTION_DAYS)
    await db.execute(
        update(RefreshJobItem)
        .where(
            RefreshJobItem.status == "running",
            RefreshJobItem.lease_expires_at <= datetime.now(timezone.utc),
        )
        .values(status="queued", lease_token=None, lease_expires_at=None)
    )
    await db.execute(
        update(RefreshJob)
        .where(RefreshJob.status == "running", ~RefreshJob.items.any(RefreshJobItem.status == "running"))
        .values(status="queued", started_at=None)
    )
    await db.execute(
        update(RefreshJob)
        .where(RefreshJob.status == "queued", RefreshJob.total == 0)
        .values(status="completed", finished_at=datetime.now(timezone.utc))
    )
    await db.execute(
        text("DELETE FROM refresh_jobs WHERE status IN ('completed', 'failed') AND finished_at < :cutoff"),
        {"cutoff": cutoff},
    )
    ranked_snapshots = (
        select(
            PageSnapshot.id.label("id"),
            func.row_number().over(
                partition_by=PageSnapshot.page_id,
                order_by=(PageSnapshot.fetched_at.desc(), PageSnapshot.id.desc()),
            ).label("row_number"),
        )
        .subquery()
    )
    excess_snapshot_ids = select(ranked_snapshots.c.id).where(
        ranked_snapshots.c.row_number > settings.PAGE_SNAPSHOT_MAX_PER_PAGE
    )
    await db.execute(
        delete(PageSnapshot).where(
            or_(
                PageSnapshot.fetched_at < snapshot_cutoff,
                PageSnapshot.id.in_(excess_snapshot_ids),
            )
        )
    )
    await db.commit()
