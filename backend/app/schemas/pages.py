from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class AddPageRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=255)

    model_config = ConfigDict(extra="forbid")


class PageResponse(BaseModel):
    id: UUID
    username: str
    status: str = "ready"
    source: str = "official"  # "official" or "backup"
    fallback_reason: Optional[str] = None
    error_kind: Optional[str] = None
    error_message: Optional[str] = None
    followers: int
    last_reel_likes: Optional[int] = None
    last_reel_views: Optional[int] = None
    avg_views: float
    median_views: float
    avg_likes: float
    like_to_view_ratio: float
    avg_views_per_follower: float
    reels_sampled: int
    last_refreshed_at: Optional[datetime] = None
    last_refresh_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RefreshAllJobResponse(BaseModel):
    job_id: str
    total: int
    done: int
    failed: int
    status: str
