from datetime import datetime, timezone, timedelta
from typing import List, Tuple, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select, update, delete, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.core.security import normalize_username, validate_username_format
from app.db.models import Page, PageSnapshot, PageTag
from app.db.session import AsyncSessionLocal
from app.services.business_discovery import IGError, Kind
from app.services.metrics import compute_metrics
from app.services.providers.chain import provider_chain
from app.services import refresh_jobs

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
    order: str = "desc",
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None,
) -> Tuple[List[Page], int, int, int, float]:
    sort_col = ALLOWED_SORT_FIELDS.get(sort_by.lower(), Page.followers)
    is_desc = (order.lower() == "desc")
    if is_desc:
        ordering = (sort_col.desc().nulls_last(), Page.id.asc())
    else:
        ordering = (sort_col.asc().nulls_last(), Page.id.asc())

    filters = [Page.user_id == user_id]
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        tagged_page_ids = select(PageTag.page_id).where(PageTag.label.ilike(pattern))
        filters.append(or_(Page.username.ilike(pattern), Page.id.in_(tagged_page_ids)))

    total_result = await db.execute(select(func.count(Page.id)).where(*filters))
    total = int(total_result.scalar_one())
    summary_result = await db.execute(
        select(
            func.count(Page.id),
            func.coalesce(func.sum(Page.followers), 0),
            func.coalesce(func.avg(Page.avg_views_per_follower), 0.0),
        ).where(Page.user_id == user_id)
    )
    workspace_page_count, total_followers, average_views_per_follower = summary_result.one()

    stmt = (
        select(Page)
        .where(*filters)
        .order_by(*ordering)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    return (
        list(result.scalars().all()),
        total,
        int(workspace_page_count),
        int(total_followers or 0),
        float(average_views_per_follower or 0.0),
    )


async def update_page_tags(db: AsyncSession, user_id: UUID, page_id: UUID, labels: List[str]) -> Page:
    stmt = select(Page).where(Page.id == page_id, Page.user_id == user_id)
    result = await db.execute(stmt)
    page = result.scalar_one_or_none()
    if page is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PAGE_NOT_FOUND", "message": "Page not found or does not belong to your agency."},
        )
    page.tag_items = [PageTag(label=label) for label in labels]
    await db.commit()
    await db.refresh(page)
    return page


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

    await db.flush()
    await refresh_jobs.enqueue_page_refresh(db, user_id, page.id)
    await db.refresh(page)
    return page, created


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


async def delete_page(db: AsyncSession, user_id: UUID, page_id: UUID) -> None:
    stmt = select(Page).where(Page.id == page_id, Page.user_id == user_id)
    res = await db.execute(stmt)
    page = res.scalar_one_or_none()
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PAGE_NOT_FOUND", "message": "Page not found or does not belong to your agency."}
        )
    await db.execute(delete(PageSnapshot).where(PageSnapshot.page_id == page.id))
    await db.delete(page)
    await db.commit()


