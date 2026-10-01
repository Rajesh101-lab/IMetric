import math
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Request, Response, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, verify_csrf
from app.db.session import get_db
from app.db.models import User
from app.core.config import settings
from app.schemas.pages import AddPageRequest, PageListResponse, PageResponse, PageTagsRequest, RefreshAllJobResponse, PageSummary
from app.services import pages as pages_service, refresh_jobs

router = APIRouter(prefix="/pages", tags=["pages"])


@router.get("", response_model=PageListResponse)
async def list_pages(
    sort: str = Query(default="followers", description="Field to sort by"),
    order: str = Query(default="desc", description="Sort order: asc or desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.PAGE_DEFAULT_SIZE, ge=1, le=settings.PAGE_MAX_SIZE),
    q: Optional[str] = Query(default=None, max_length=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns list of pages belonging strictly to the current agency user.
    Includes status ('pending', 'ready', 'failed'), error_kind, error_message, and last_refreshed_at.
    """
    pages, total, workspace_page_count, total_followers, average_views_per_follower = await pages_service.list_user_pages(
        db,
        current_user.id,
        sort_by=sort,
        order=order,
        page=page,
        page_size=page_size,
        search=q,
    )
    return PageListResponse(
        items=[PageResponse.model_validate(item) for item in pages],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
        summary=PageSummary(
            total_pages=workspace_page_count,
            total_followers=total_followers,
            avg_views_per_follower=average_views_per_follower,
        ),
    )


@router.post("", response_model=PageResponse, status_code=status.HTTP_202_ACCEPTED)
async def add_page(
    req: AddPageRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Normalizes username, inserts Page row with status='pending',
    launches background fetch task, and returns 202 Accepted immediately.
    """
    verify_csrf(request)
    page, created = await pages_service.add_or_upsert_page(db, current_user.id, req.username)
    return PageResponse.model_validate(page)


@router.put("/{page_id}/tags", response_model=PageResponse)
async def update_page_tags(
    page_id: UUID,
    req: PageTagsRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    verify_csrf(request)
    page = await pages_service.update_page_tags(db, current_user.id, page_id, req.tags)
    return PageResponse.model_validate(page)


@router.post("/{page_id}/refresh", response_model=PageResponse)
async def refresh_page(
    page_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Re-fetches metrics for one of the agency's pages, updates row, appends snapshot.
    Enforces 60-second per-page refresh cooldown.
    """
    verify_csrf(request)
    page = await pages_service.refresh_single_page(db, current_user.id, page_id)
    return PageResponse.model_validate(page)


@router.delete("/{page_id}")
async def remove_page(
    page_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    verify_csrf(request)
    await pages_service.delete_page(db, current_user.id, page_id)
    return {"message": "Page removed successfully."}


@router.post("/refresh-all", response_model=RefreshAllJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def refresh_all_pages(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers background refresh of all current user pages with bounded concurrency (202 Accepted).
    """
    verify_csrf(request)
    job_info = await refresh_jobs.create_refresh_job(db, current_user.id)
    return RefreshAllJobResponse(**job_info)


@router.get("/refresh-all/current", response_model=Optional[RefreshAllJobResponse])
async def get_current_refresh_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job_info = await refresh_jobs.get_active_refresh_job(db, current_user.id)
    return RefreshAllJobResponse(**job_info) if job_info else None


@router.get("/refresh-all/{job_id}", response_model=RefreshAllJobResponse)
async def get_refresh_all_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns durable status for a job owned by the current workspace."""
    job_info = await refresh_jobs.get_refresh_job(db, current_user.id, job_id)
    return RefreshAllJobResponse(**job_info)
