from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, verify_csrf
from app.db.models import User
from app.db.session import get_db
from app.schemas.campaigns import CampaignRequest, CampaignResponse
from app.services import campaigns as campaigns_service

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("", response_model=List[CampaignResponse])
async def list_campaigns(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    campaigns = await campaigns_service.list_campaigns(db, current_user.id)
    return [CampaignResponse.model_validate(campaign) for campaign in campaigns]


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    req: CampaignRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    verify_csrf(request)
    campaign = await campaigns_service.create_campaign(db, current_user.id, req)
    return CampaignResponse.model_validate(campaign)


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    req: CampaignRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    verify_csrf(request)
    campaign = await campaigns_service.update_campaign(db, current_user.id, campaign_id, req)
    return CampaignResponse.model_validate(campaign)


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    verify_csrf(request)
    await campaigns_service.delete_campaign(db, current_user.id, campaign_id)
    return {"message": "Campaign removed successfully."}