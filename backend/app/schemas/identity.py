from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProfileUpdate(BaseModel):
    display_name: str = Field(min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=32)


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    display_name: str
    email: str | None
    phone: str | None
    is_active: bool
    must_change_password: bool
    account_status: str
    email_verified: bool
    created_at: datetime


class ProvisionProfile(BaseModel):
    user_id: UUID
    display_name: str = Field(min_length=1, max_length=200)
    role_names: list[str] = Field(min_length=1, max_length=5)
