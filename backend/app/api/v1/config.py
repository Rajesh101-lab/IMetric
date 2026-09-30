from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.core.config import settings
from app.db.models import User
from app.schemas.config import ConfigResponse

router = APIRouter(prefix="/config", tags=["config"])


@router.get("", response_model=ConfigResponse)
async def get_app_config(
    current_user: User = Depends(get_current_user)
):
    """
    Returns non-sensitive app configuration settings (e.g., whether backup source is enabled).
    Does NOT leak API keys or secret limits.
    """
    return ConfigResponse(backup_enabled=settings.BACKUP_ENABLED)
