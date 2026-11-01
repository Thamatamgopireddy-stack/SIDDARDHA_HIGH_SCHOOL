from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.exceptions import APIError
from app.core.security import verified_claims
from app.db.session import get_db
from app.models.identity import Role, UserProfile, UserRole


@dataclass(frozen=True)
class CurrentUser:
    id: UUID
    school_id: UUID
    display_name: str
    email: str | None
    active: bool
    account_status: str
    role_names: frozenset[str]

    @property
    def is_super_admin(self) -> bool:
        return "super_admin" in self.role_names


async def get_current_user(
    claims: Annotated[dict[str, object], Depends(verified_claims)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurrentUser:
    user_id = UUID(str(claims["sub"]))
    await db.execute(
        text("SELECT set_config('app.user_id', :user_id, true)"),
        {"user_id": str(user_id)},
    )
    profile = await db.scalar(select(UserProfile).where(UserProfile.id == user_id))
    if profile is None:
        raise APIError(
            status.HTTP_403_FORBIDDEN,
            "PROFILE_UNAVAILABLE",
            "Your account has no school profile. Submit a verified registration request.",
        )
    await db.execute(
        text("SELECT set_config('app.school_id', :school_id, true)"),
        {"school_id": str(profile.school_id)},
    )
    role_query = (
        select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id, UserRole.is_active.is_(True))
    )
    role_names = frozenset((await db.scalars(role_query)).all())
    if profile.account_status != "approved" or not profile.is_active or not profile.email_verified:
        if not profile.email_verified:
            raise APIError(
                status.HTTP_403_FORBIDDEN,
                "EMAIL_VERIFICATION_REQUIRED",
                "Verify your email address before accessing the ERP.",
            )
        code = {
            "pending": "APPROVAL_PENDING",
            "rejected": "REGISTRATION_REJECTED",
            "suspended": "ACCOUNT_SUSPENDED",
            "disabled": "ACCOUNT_DISABLED",
        }.get(profile.account_status, "ACCOUNT_NOT_APPROVED")
        raise APIError(
            status.HTTP_403_FORBIDDEN,
            code,
            "Your account is not approved for ERP access.",
        )
    return CurrentUser(
        id=profile.id,
        school_id=profile.school_id,
        display_name=profile.display_name,
        email=profile.email,
        active=profile.is_active,
        account_status=profile.account_status,
        role_names=role_names,
    )


async def require_super_admin(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    if not user.is_super_admin:
        raise APIError(
            status.HTTP_403_FORBIDDEN,
            "SUPER_ADMIN_REQUIRED",
            "Only the Super Admin can perform this operation.",
        )
    return user
