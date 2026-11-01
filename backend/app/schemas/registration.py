from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class RegistrationBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    phone_number: str = Field(min_length=7, max_length=32)
    employee_id: str | None = Field(default=None, max_length=64)
    department: str = Field(min_length=1, max_length=120)
    designation: str = Field(min_length=1, max_length=120)


class AdminRegistration(RegistrationBase):
    employee_id: str | None = Field(default=None, max_length=64)


class StaffRegistration(RegistrationBase):
    employee_id: str = Field(min_length=1, max_length=64)
    staff_category: str = Field(min_length=1, max_length=64)


class RegistrationRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    applicant_user_id: UUID
    full_name: str
    email: str
    phone_number: str
    employee_id: str | None
    department: str
    designation: str
    staff_category: str | None
    requested_role: str
    email_verified: bool
    status: str
    rejection_reason: str | None
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class RegistrationStatus(BaseModel):
    account_status: str
    email_verified: bool
    full_name: str
    email: str
    requested_role: str | None
    rejection_reason: str | None
    created_at: datetime | None
    roles: list[str]
    permissions: list[str]
    portal: str | None


class ApprovalDecision(BaseModel):
    reason: str | None = Field(default=None, min_length=5, max_length=1000)

    @model_validator(mode="after")
    def reject_blank_reason(self) -> "ApprovalDecision":
        if self.reason is not None and not self.reason.strip():
            raise ValueError("Rejection reason cannot be blank")
        return self


class AccountStatusUpdate(BaseModel):
    account_status: str = Field(pattern="^(approved|suspended|disabled|pending)$")
    reason: str = Field(min_length=5, max_length=1000)


class PermissionUpdate(BaseModel):
    permission_names: list[str] = Field(max_length=100)


class AccountUserRead(BaseModel):
    id: UUID
    full_name: str
    email: str | None
    phone_number: str | None
    account_status: str
    roles: list[str]
    permissions: list[str]
    created_at: datetime


class ApprovalCounts(BaseModel):
    total_requests: int
    pending_admin_requests: int
    pending_staff_requests: int
    approved_accounts: int
    rejected_requests: int
    suspended_accounts: int


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_user_id: UUID | None
    target_user_id: UUID | None
    action: str
    previous_status: str | None
    new_status: str | None
    description: str
    created_at: datetime
