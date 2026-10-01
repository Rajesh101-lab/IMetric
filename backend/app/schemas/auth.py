import re
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from uuid import UUID


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)

    model_config = ConfigDict(extra="forbid")


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=30)
    password: str = Field(..., min_length=12, max_length=128)
    contact_email: str = Field(..., min_length=3, max_length=254)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("contact_email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        email = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            raise ValueError("Enter a valid contact email address.")
        return email

    model_config = ConfigDict(extra="forbid")


class UserResponse(BaseModel):
    id: UUID
    username: str
    is_admin: bool = False

    model_config = ConfigDict(from_attributes=True)


class CSRFResponse(BaseModel):
    csrf_token: str


class MessageResponse(BaseModel):
    message: str


class RegistrationSubmissionResponse(BaseModel):
    username: str
    status: str


class RegistrationRequestResponse(BaseModel):
    id: UUID
    username: str
    contact_email: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
