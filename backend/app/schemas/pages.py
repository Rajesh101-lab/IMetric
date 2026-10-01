from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class AddPageRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=255)

    model_config = ConfigDict(extra="forbid")


class PageTagsRequest(BaseModel):
    tags: List[str] = Field(default_factory=list, max_length=12)

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, tags: List[str]) -> List[str]:
        normalized = []
        seen = set()
        for raw_tag in tags:
            tag = raw_tag.strip()
            if not tag or len(tag) > 32:
                raise ValueError("Tags must contain between 1 and 32 characters.")
            key = tag.casefold()
            if key not in seen:
                normalized.append(tag)
                seen.add(key)
        return normalized

    model_config = ConfigDict(extra="forbid")


class PageResponse(BaseModel):
    id: UUID
    username: str
    tags: List[str] = Field(default_factory=list)
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


class PageSummary(BaseModel):
    total_pages: int
    total_followers: int
    avg_views_per_follower: float


class PageListResponse(BaseModel):
    items: List[PageResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    summary: PageSummary


class RefreshAllJobResponse(BaseModel):
    job_id: str
    total: int
    done: int
    failed: int
    status: str
