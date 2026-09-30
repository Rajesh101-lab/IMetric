from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)

    model_config = ConfigDict(extra="forbid")


class UserResponse(BaseModel):
    id: UUID
    username: str

    model_config = ConfigDict(from_attributes=True)


class CSRFResponse(BaseModel):
    csrf_token: str


class MessageResponse(BaseModel):
    message: str
