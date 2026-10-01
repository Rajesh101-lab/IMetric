from typing import List
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Campaign, Page
from app.schemas.campaigns import CampaignRequest


async def _owned_pages(db: AsyncSession, user_id: UUID, page_ids: List[UUID]) -> List[Page]:
    unique_ids = list(dict.fromkeys(page_ids))
    if not unique_ids:
        return []

    result = await db.execute(select(Page).where(Page.user_id == user_id, Page.id.in_(unique_ids)))
    pages_by_id = {page.id: page for page in result.scalars().all()}
    if len(pages_by_id) != len(unique_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PAGE_NOT_FOUND", "message": "One or more pages are not in your workspace."},
        )
    return [pages_by_id[page_id] for page_id in unique_ids]


async def list_campaigns(db: AsyncSession, user_id: UUID) -> List[Campaign]:
    result = await db.execute(
        select(Campaign).where(Campaign.user_id == user_id).order_by(Campaign.created_at.desc())
    )
    return list(result.scalars().all())


async def create_campaign(db: AsyncSession, user_id: UUID, request: CampaignRequest) -> Campaign:
    pages = await _owned_pages(db, user_id, request.page_ids)
    campaign = Campaign(
        user_id=user_id,
        name=request.name,
        description=request.description,
        pages=pages,
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign


async def update_campaign(
    db: AsyncSession, user_id: UUID, campaign_id: UUID, request: CampaignRequest
) -> Campaign:
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == user_id)
    )
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise HTTPException(status_code=404, detail={"code": "CAMPAIGN_NOT_FOUND", "message": "Campaign not found."})

    campaign.name = request.name
    campaign.description = request.description
    campaign.pages = await _owned_pages(db, user_id, request.page_ids)
    await db.commit()
    await db.refresh(campaign)
    return campaign


async def delete_campaign(db: AsyncSession, user_id: UUID, campaign_id: UUID) -> None:
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == user_id)
    )
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise HTTPException(status_code=404, detail={"code": "CAMPAIGN_NOT_FOUND", "message": "Campaign not found."})
    await db.delete(campaign)
    await db.commit()