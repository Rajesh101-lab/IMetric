from pydantic import BaseModel


class ConfigResponse(BaseModel):
    backup_enabled: bool
