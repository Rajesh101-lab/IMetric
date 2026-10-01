from pydantic import BaseModel


class ConfigResponse(BaseModel):
    backup_enabled: bool
    official_api_configured: bool
