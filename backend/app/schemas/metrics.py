from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class PageMetrics(BaseModel):
    username: str
    followers: int = Field(ge=0)
    lastreellikes: Optional[int] = Field(default=None, ge=0)
    lastreelviews: Optional[int] = Field(default=None, ge=0)
    avgviews: float = Field(ge=0.0)
    medianviews: float = Field(ge=0.0)
    avglikes: float = Field(ge=0.0)
    liketoviewratio: float = Field(ge=0.0)
    avgviewsperfollower: float = Field(ge=0.0)
    reelssampled: int = Field(ge=0)
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(extra="forbid")
