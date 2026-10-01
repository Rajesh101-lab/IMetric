from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CampaignRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    description: Optional[str] = Field(default=None, max_length=255)
    page_ids: List[UUID] = Field(default_factory=list, max_length=500)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: Optional[str]) -> Optional[str]:
        if isinstance(value, str):
            return value.strip() or None
        return value

    model_config = ConfigDict(extra="forbid")


class CampaignResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    page_ids: List[UUID]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)