from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Request, Response, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, verify_csrf
from app.db.session import get_db
from app.db.models import User
from app.schemas.pages import AddPageRequest, PageResponse, RefreshAllJobResponse
from app.services import pages as pages_service

router = APIRouter(prefix="/pages", tags=["pages"])


@router.get("", response_model=List[PageResponse])
async def list_pages(
    sort: str = Query(default="followers", description="Field to sort by"),
    order: str = Query(default="desc", description="Sort order: asc or desc"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns list of pages belonging strictly to the current agency user.
    Includes status ('pending', 'ready', 'failed'), error_kind, error_message, and last_refreshed_at.
    """
    pages = await pages_service.list_user_pages(db, current_user.id, sort_by=sort, order=order)
    return [PageResponse.model_validate(p) for p in pages]


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
    job_info = await pages_service.start_refresh_all_job(db, current_user.id)
    return RefreshAllJobResponse(**job_info)


@router.get("/refresh-all/{job_id}", response_model=RefreshAllJobResponse)
async def get_refresh_all_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Polls status of ongoing refresh-all job for current user.
    """
    job_info = pages_service.get_refresh_all_job_status(current_user.id, job_id)
    return RefreshAllJobResponse(**job_info)
