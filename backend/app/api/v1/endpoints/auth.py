from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.config import Settings, get_settings
from app.core.exceptions import APIError
from app.db.session import get_scoped_db
from app.dependencies.auth import CurrentUser, get_current_user, require_super_admin
from app.integrations.supabase.admin import fetch_auth_user
from app.models.identity import (
    Permission,
    Role,
    RolePermission,
    UserPermission,
    UserProfile,
    UserRole,
)
from app.models.operations import AuditLog, School
from app.schemas.common import SuccessEnvelope
from app.schemas.identity import ProfileRead, ProfileUpdate, ProvisionProfile

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/me", response_model=SuccessEnvelope[ProfileRead])
async def read_me(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
) -> SuccessEnvelope[ProfileRead]:
    profile = await db.get(UserProfile, user.id)
    if profile is None:
        raise APIError(status.HTTP_404_NOT_FOUND, "PROFILE_NOT_FOUND", "Profile not found")
    return SuccessEnvelope(data=ProfileRead.model_validate(profile))


@router.get("/permissions", response_model=SuccessEnvelope[list[str]])
async def read_permissions(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
) -> SuccessEnvelope[list[str]]:
    statement = (
        select(Permission.name)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .where(UserRole.user_id == user.id, UserRole.is_active.is_(True))
        .distinct()
        .order_by(Permission.name)
    )
    role_permissions = set((await db.scalars(statement)).all())
    direct_statement = (
        select(Permission.name)
        .join(UserPermission, UserPermission.permission_id == Permission.id)
        .where(UserPermission.user_id == user.id)
    )
    role_permissions.update((await db.scalars(direct_statement)).all())
    return SuccessEnvelope(data=sorted(role_permissions))


@router.patch("/profile", response_model=SuccessEnvelope[ProfileRead])
async def update_profile(
    payload: ProfileUpdate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
) -> SuccessEnvelope[ProfileRead]:
    profile = await db.get(UserProfile, user.id)
    if profile is None:
        raise APIError(status.HTTP_404_NOT_FOUND, "PROFILE_NOT_FOUND", "Profile not found")
    profile.display_name = payload.display_name
    profile.phone = payload.phone
    db.add(
        AuditLog(
            school_id=user.school_id,
            actor_id=user.id,
            action="profile.updated",
            resource_type="user_profile",
            resource_id=profile.id,
        )
    )
    await db.commit()
    await db.refresh(profile)
    return SuccessEnvelope(data=ProfileRead.model_validate(profile), message="Profile updated")


@router.post(
    "/provision-profile",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessEnvelope[ProfileRead],
)
async def provision_profile(
    payload: ProvisionProfile,
    user: Annotated[CurrentUser, Depends(require_super_admin)],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SuccessEnvelope[ProfileRead]:
    existing = await db.get(UserProfile, payload.user_id)
    if existing is not None:
        raise APIError(status.HTTP_409_CONFLICT, "PROFILE_EXISTS", "Profile already exists")
    if await db.get(School, user.school_id) is None:
        raise APIError(status.HTTP_409_CONFLICT, "SCHOOL_UNAVAILABLE", "School is unavailable")
    roles = list(
        (
            await db.scalars(
                select(Role).where(
                    Role.school_id == user.school_id,
                    Role.name.in_(set(payload.role_names) - {"super_admin"}),
                )
            )
        ).all()
    )
    if len(roles) != len(set(payload.role_names)):
        raise APIError(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "INVALID_ROLE", "One or more roles are invalid"
        )
    auth_user = await fetch_auth_user(payload.user_id, settings)
    if auth_user.get("email_verified") is not True:
        raise APIError(
            status.HTTP_403_FORBIDDEN,
            "EMAIL_VERIFICATION_REQUIRED",
            "The Supabase Auth user must have a verified email.",
        )
    profile = UserProfile(
        id=payload.user_id,
        school_id=user.school_id,
        display_name=payload.display_name,
        email=auth_user.get("email"),
        is_active=True,
        account_status="approved",
        email_verified=True,
    )
    db.add(profile)
    await db.flush()
    db.add_all([UserRole(user_id=profile.id, role_id=role.id) for role in roles])
    db.add(
        AuditLog(
            school_id=user.school_id,
            actor_id=user.id,
            action="profile.provisioned",
            resource_type="user_profile",
            resource_id=profile.id,
        )
    )
    await db.commit()
    await db.refresh(profile)
    return SuccessEnvelope(data=ProfileRead.model_validate(profile), message="Profile provisioned")
