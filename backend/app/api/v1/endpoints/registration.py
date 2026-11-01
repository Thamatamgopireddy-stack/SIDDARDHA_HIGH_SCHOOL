from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.config import Settings, get_settings
from app.core.exceptions import APIError
from app.core.security import verified_claims
from app.db.session import get_db, get_scoped_db
from app.dependencies.auth import CurrentUser, require_super_admin
from app.integrations.supabase.admin import fetch_auth_user
from app.models.identity import (
    AccountAuditLog,
    Permission,
    RegistrationRequest,
    Role,
    RolePermission,
    SystemSetting,
    UserPermission,
    UserProfile,
    UserRole,
)
from app.models.operations import School
from app.schemas.common import SuccessEnvelope
from app.schemas.registration import (
    AccountStatusUpdate,
    AccountUserRead,
    AdminRegistration,
    ApprovalCounts,
    ApprovalDecision,
    AuditLogRead,
    PermissionUpdate,
    RegistrationRequestRead,
    RegistrationStatus,
    StaffRegistration,
)
from app.services.email_notifications import send_account_email
from app.services.registration_service import submit_registration

router = APIRouter(prefix="/registration", tags=["registration"])
auth_router = APIRouter(prefix="/auth", tags=["authentication"])


async def _role_names(db: AsyncSession, user_id: UUID) -> list[str]:
    return sorted(
        (
            await db.scalars(
                select(Role.name)
                .join(UserRole, UserRole.role_id == Role.id)
                .where(UserRole.user_id == user_id, UserRole.is_active.is_(True))
            )
        ).all()
    )


async def _permission_names(db: AsyncSession, user_id: UUID) -> list[str]:
    role_names = (
        await db.scalars(
            select(Permission.name)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(UserRole.user_id == user_id, UserRole.is_active.is_(True))
        )
    ).all()
    direct_names = (
        await db.scalars(
            select(Permission.name)
            .join(UserPermission, UserPermission.permission_id == Permission.id)
            .where(UserPermission.user_id == user_id)
        )
    ).all()
    return sorted(set(role_names) | set(direct_names))


def _portal(roles: list[str]) -> str | None:
    if "super_admin" in roles:
        return "super_admin"
    if "admin" in roles or "administrator" in roles:
        return "admin"
    if "staff" in roles:
        return "staff"
    return None


@router.post(
    "/admin",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessEnvelope[RegistrationRequestRead],
)
async def request_admin_registration(
    payload: AdminRegistration,
    claims: Annotated[dict[str, object], Depends(verified_claims)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SuccessEnvelope[RegistrationRequestRead]:
    request = await submit_registration(
        payload=payload,
        role="admin",
        user_id=UUID(str(claims["sub"])),
        db=db,
        settings=settings,
    )
    await db.commit()
    await db.refresh(request)
    notification = await send_account_email(
        recipient=request.email,
        subject="EduCore registration request received",
        body=(
            f"Hello {request.full_name},\n\n"
            "Your email has been verified and your registration request was received. "
            "The school will contact you after reviewing it.\n"
        ),
        settings=settings,
    )
    return SuccessEnvelope(
        data=RegistrationRequestRead.model_validate(request),
        meta={"email_notification": notification},
    )


@router.post(
    "/staff",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessEnvelope[RegistrationRequestRead],
)
async def request_staff_registration(
    payload: StaffRegistration,
    claims: Annotated[dict[str, object], Depends(verified_claims)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SuccessEnvelope[RegistrationRequestRead]:
    request = await submit_registration(
        payload=payload,
        role="staff",
        user_id=UUID(str(claims["sub"])),
        db=db,
        settings=settings,
    )
    await db.commit()
    await db.refresh(request)
    notification = await send_account_email(
        recipient=request.email,
        subject="EduCore registration request received",
        body=(
            f"Hello {request.full_name},\n\n"
            "Your email has been verified and your registration request was received. "
            "The school will contact you after reviewing it.\n"
        ),
        settings=settings,
    )
    return SuccessEnvelope(
        data=RegistrationRequestRead.model_validate(request),
        meta={"email_notification": notification},
    )


@auth_router.get("/status", response_model=SuccessEnvelope[RegistrationStatus])
async def read_account_status(
    claims: Annotated[dict[str, object], Depends(verified_claims)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SuccessEnvelope[RegistrationStatus]:
    user_id = UUID(str(claims["sub"]))
    auth_user = await fetch_auth_user(user_id, settings)
    await db.execute(
        text("SELECT set_config('app.user_id', :user_id, true)"), {"user_id": str(user_id)}
    )
    profile = await db.get(UserProfile, user_id)
    if profile is None:
        return SuccessEnvelope(
            data=RegistrationStatus(
                account_status="not_registered",
                email_verified=auth_user.get("email_verified") is True,
                full_name="",
                email=str(auth_user.get("email") or ""),
                requested_role=None,
                rejection_reason=None,
                created_at=None,
                roles=[],
                permissions=[],
                portal=None,
            )
        )
    if profile.school_id:
        await db.execute(
            text("SELECT set_config('app.school_id', :school_id, true)"),
            {"school_id": str(profile.school_id)},
        )
    latest_request = await db.scalar(
        select(RegistrationRequest)
        .where(RegistrationRequest.applicant_user_id == user_id)
        .order_by(RegistrationRequest.created_at.desc())
        .limit(1)
    )
    email_verified = profile.email_verified and auth_user.get("email_verified") is True
    account_status = profile.account_status
    if not email_verified and account_status == "approved":
        account_status = "pending_email_verification"
    roles = await _role_names(db, user_id) if account_status == "approved" else []
    permissions = await _permission_names(db, user_id) if roles else []
    return SuccessEnvelope(
        data=RegistrationStatus(
            account_status=account_status,
            email_verified=email_verified,
            full_name=profile.display_name,
            email=profile.email or str(auth_user.get("email") or ""),
            requested_role=latest_request.requested_role if latest_request else None,
            rejection_reason=latest_request.rejection_reason if latest_request else None,
            created_at=latest_request.created_at if latest_request else profile.created_at,
            roles=roles,
            permissions=permissions,
            portal=_portal(roles),
        )
    )


@auth_router.post("/bootstrap-super-admin", response_model=SuccessEnvelope[RegistrationStatus])
async def bootstrap_super_admin(
    claims: Annotated[dict[str, object], Depends(verified_claims)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SuccessEnvelope[RegistrationStatus]:
    if not settings.super_admin_email or not settings.school_id:
        raise APIError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "BOOTSTRAP_NOT_CONFIGURED",
            "Super Admin bootstrap is not configured.",
        )
    try:
        school_id = UUID(settings.school_id)
        user_id = UUID(str(claims["sub"]))
    except ValueError as exc:
        raise APIError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "BOOTSTRAP_NOT_CONFIGURED",
            "Super Admin bootstrap configuration is invalid.",
        ) from exc
    auth_user = await fetch_auth_user(user_id, settings)
    email = auth_user.get("email")
    if (
        auth_user.get("email_verified") is not True
        or not isinstance(email, str)
        or email.casefold() != settings.super_admin_email
    ):
        raise APIError(
            status.HTTP_403_FORBIDDEN,
            "OWNER_EMAIL_REQUIRED",
            "Only the verified configured owner email can claim the Super Admin role.",
        )

    async with db.begin():
        await db.execute(
            text("SELECT set_config('app.user_id', :user_id, true)"), {"user_id": str(user_id)}
        )
        await db.execute(
            text("SELECT set_config('app.school_id', :school_id, true)"),
            {"school_id": str(school_id)},
        )
        await db.execute(text("SELECT set_config('app.is_super_admin', 'true', true)"))
        school = await db.get(School, school_id)
        if school is None or not school.is_active:
            raise APIError(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "SCHOOL_NOT_CONFIGURED",
                "School bootstrap must be completed by the database owner first.",
            )
        setting = await db.scalar(
            select(SystemSetting)
            .where(SystemSetting.key == "super_admin_bootstrap_completed")
            .with_for_update()
        )
        if setting is None:
            raise APIError(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "BOOTSTRAP_NOT_CONFIGURED",
                "The one-time bootstrap setting is missing. Run the database migrations.",
            )
        if setting.value.casefold() != "false":
            raise APIError(
                status.HTTP_409_CONFLICT,
                "BOOTSTRAP_ALREADY_COMPLETED",
                "The one-time Super Admin bootstrap has already been completed.",
            )

        profile = await db.get(UserProfile, user_id)
        if profile is not None and profile.school_id != school_id:
            raise APIError(
                status.HTTP_409_CONFLICT,
                "PROFILE_SCHOOL_CONFLICT",
                "This account is already assigned to a different school.",
            )
        if profile is None:
            profile = UserProfile(
                id=user_id,
                school_id=school_id,
                display_name=_display_name(claims, email),
                email=email.casefold(),
                account_status="approved",
                email_verified=True,
                is_active=True,
            )
            db.add(profile)
            await db.flush()
        else:
            profile.email = email.casefold()
            profile.email_verified = True
            profile.account_status = "approved"
            profile.is_active = True

        roles: dict[str, Role] = {}
        for name in ("super_admin", "admin", "staff"):
            role = await db.scalar(
                select(Role).where(Role.school_id == school_id, Role.name == name)
            )
            if role is None:
                role = Role(school_id=school_id, name=name)
                db.add(role)
                await db.flush()
            roles[name] = role
        assigned = await db.scalar(
            select(UserRole.id).where(
                UserRole.user_id == user_id, UserRole.role_id == roles["super_admin"].id
            )
        )
        if assigned is None:
            db.add(
                UserRole(
                    user_id=user_id,
                    role_id=roles["super_admin"].id,
                    assigned_by=user_id,
                    is_active=True,
                )
            )
        all_permissions = list((await db.scalars(select(Permission))).all())
        if not all_permissions:
            raise APIError(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "PERMISSIONS_NOT_CONFIGURED",
                "Seed school permissions before completing Super Admin bootstrap.",
            )
        existing_pairs = set(
            (
                await db.execute(
                    select(RolePermission.role_id, RolePermission.permission_id).where(
                        RolePermission.role_id == roles["super_admin"].id
                    )
                )
            ).all()
        )
        db.add_all(
            [
                RolePermission(role_id=roles["super_admin"].id, permission_id=permission.id)
                for permission in all_permissions
                if (roles["super_admin"].id, permission.id) not in existing_pairs
            ]
        )
        setting.value = "true"
        db.add(
            AccountAuditLog(
                school_id=school_id,
                actor_user_id=user_id,
                target_user_id=user_id,
                action="super_admin.bootstrap",
                previous_status=None,
                new_status="approved",
                description="Owner completed one-time Super Admin bootstrap.",
            )
        )

    return SuccessEnvelope(
        data=RegistrationStatus(
            account_status="approved",
            email_verified=True,
            full_name=profile.display_name,
            email=email.casefold(),
            requested_role=None,
            rejection_reason=None,
            created_at=profile.created_at,
            roles=["super_admin"],
            permissions=sorted(permission.name for permission in all_permissions),
            portal="super_admin",
        ),
        message="Super Admin account bootstrapped.",
    )


@router.get(
    "/requests",
    response_model=SuccessEnvelope[list[RegistrationRequestRead]],
)
async def list_registration_requests(
    user: Annotated[CurrentUser, Depends(require_super_admin)],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
    request_status: Annotated[
        str, Query(alias="status", pattern="^(pending|approved|rejected)$")
    ] = "pending",
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> SuccessEnvelope[list[RegistrationRequestRead]]:
    requests = (
        await db.scalars(
            select(RegistrationRequest)
            .where(
                RegistrationRequest.school_id == user.school_id,
                RegistrationRequest.status == request_status,
            )
            .order_by(RegistrationRequest.created_at.asc())
            .limit(limit)
        )
    ).all()
    return SuccessEnvelope(
        data=[RegistrationRequestRead.model_validate(request) for request in requests]
    )


@router.post(
    "/requests/{request_id}/approve",
    response_model=SuccessEnvelope[RegistrationRequestRead],
)
async def approve_registration(
    request_id: UUID,
    user: Annotated[CurrentUser, Depends(require_super_admin)],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SuccessEnvelope[RegistrationRequestRead]:
    request = await db.scalar(
        select(RegistrationRequest)
        .where(
            RegistrationRequest.id == request_id,
            RegistrationRequest.school_id == user.school_id,
        )
        .with_for_update()
    )
    if request is None:
        raise APIError(
            status.HTTP_404_NOT_FOUND, "REQUEST_NOT_FOUND", "Registration request not found."
        )
    if request.status != "pending":
        raise APIError(
            status.HTTP_409_CONFLICT,
            "REQUEST_ALREADY_REVIEWED",
            "This registration request has already been reviewed.",
        )
    profile = await db.get(UserProfile, request.applicant_user_id)
    role_name = request.requested_role
    role = await db.scalar(
        select(Role).where(Role.school_id == user.school_id, Role.name == role_name)
    )
    if profile is None or role is None:
        raise APIError(
            status.HTTP_409_CONFLICT,
            "REGISTRATION_CONFIGURATION_ERROR",
            "The applicant profile or requested role is unavailable.",
        )
    now = datetime.now(UTC)
    request.status = "approved"
    request.reviewed_by = user.id
    request.reviewed_at = now
    request.rejection_reason = None
    profile.account_status = "approved"
    profile.is_active = True
    assigned = await db.scalar(
        select(UserRole.id).where(UserRole.user_id == profile.id, UserRole.role_id == role.id)
    )
    if assigned is None:
        db.add(UserRole(user_id=profile.id, role_id=role.id, assigned_by=user.id, is_active=True))
    else:
        assignment = await db.get(UserRole, assigned)
        if assignment is not None:
            assignment.is_active = True
            assignment.assigned_by = user.id
    db.add(
        AccountAuditLog(
            school_id=user.school_id,
            actor_user_id=user.id,
            target_user_id=profile.id,
            action="registration.approved",
            previous_status="pending",
            new_status="approved",
            description=f"Approved {role_name} registration.",
        )
    )
    await db.commit()
    await db.refresh(request)
    notification = await send_account_email(
        recipient=request.email,
        subject="EduCore account approved",
        body=(
            f"Hello {request.full_name},\n\n"
            f"Your {role_name} account has been approved. Sign in using an email one-time code at "
            f"{settings.frontend_url.rstrip('/')}/login.\n"
        ),
        settings=settings,
    )
    return SuccessEnvelope(
        data=RegistrationRequestRead.model_validate(request),
        message=f"Registration approved; email notification {notification}.",
        meta={"email_notification": notification},
    )


@router.post(
    "/requests/{request_id}/reject",
    response_model=SuccessEnvelope[RegistrationRequestRead],
)
async def reject_registration(
    request_id: UUID,
    payload: ApprovalDecision,
    user: Annotated[CurrentUser, Depends(require_super_admin)],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SuccessEnvelope[RegistrationRequestRead]:
    request = await db.scalar(
        select(RegistrationRequest)
        .where(
            RegistrationRequest.id == request_id,
            RegistrationRequest.school_id == user.school_id,
        )
        .with_for_update()
    )
    if request is None:
        raise APIError(
            status.HTTP_404_NOT_FOUND, "REQUEST_NOT_FOUND", "Registration request not found."
        )
    if request.status != "pending":
        raise APIError(
            status.HTTP_409_CONFLICT,
            "REQUEST_ALREADY_REVIEWED",
            "This registration request has already been reviewed.",
        )
    profile = await db.get(UserProfile, request.applicant_user_id)
    if profile is None:
        raise APIError(
            status.HTTP_409_CONFLICT, "PROFILE_NOT_FOUND", "Applicant profile is unavailable."
        )
    previous_status = profile.account_status
    request.status = "rejected"
    request.rejection_reason = (
        payload.reason.strip() if payload.reason else "Application was not approved."
    )
    request.reviewed_by = user.id
    request.reviewed_at = datetime.now(UTC)
    profile.account_status = "rejected"
    profile.is_active = False
    db.add(
        AccountAuditLog(
            school_id=user.school_id,
            actor_user_id=user.id,
            target_user_id=profile.id,
            action="registration.rejected",
            previous_status=previous_status,
            new_status="rejected",
            description=f"Rejected registration: {request.rejection_reason}",
        )
    )
    await db.commit()
    await db.refresh(request)
    notification = await send_account_email(
        recipient=request.email,
        subject="EduCore registration update",
        body=(
            f"Hello {request.full_name},\n\n"
            "Your registration request was not approved.\n"
            f"Review note: {request.rejection_reason}\n"
        ),
        settings=settings,
    )
    return SuccessEnvelope(
        data=RegistrationRequestRead.model_validate(request),
        message=f"Registration rejected; email notification {notification}.",
        meta={"email_notification": notification},
    )


@router.get("/users", response_model=SuccessEnvelope[list[AccountUserRead]])
async def list_school_users(
    user: Annotated[CurrentUser, Depends(require_super_admin)],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> SuccessEnvelope[list[AccountUserRead]]:
    profiles = (
        await db.scalars(
            select(UserProfile)
            .where(UserProfile.school_id == user.school_id)
            .order_by(UserProfile.created_at.desc())
            .limit(limit)
        )
    ).all()
    result: list[AccountUserRead] = []
    for profile in profiles:
        result.append(
            AccountUserRead(
                id=profile.id,
                full_name=profile.display_name,
                email=profile.email,
                phone_number=profile.phone,
                account_status=profile.account_status,
                roles=await _role_names(db, profile.id),
                permissions=await _permission_names(db, profile.id),
                created_at=profile.created_at,
            )
        )
    return SuccessEnvelope(data=result)


@router.patch("/users/{user_id}/status", response_model=SuccessEnvelope[AccountUserRead])
async def update_account_status(
    user_id: UUID,
    payload: AccountStatusUpdate,
    user: Annotated[CurrentUser, Depends(require_super_admin)],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
) -> SuccessEnvelope[AccountUserRead]:
    if user_id == user.id and payload.account_status != "approved":
        raise APIError(
            status.HTTP_409_CONFLICT,
            "CANNOT_DISABLE_SELF",
            "The Super Admin cannot suspend or disable their own account.",
        )
    profile = await db.scalar(
        select(UserProfile).where(
            UserProfile.id == user_id, UserProfile.school_id == user.school_id
        )
    )
    if profile is None:
        raise APIError(status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND", "User not found.")
    previous_status = profile.account_status
    profile.account_status = payload.account_status
    profile.is_active = payload.account_status == "approved"
    db.add(
        AccountAuditLog(
            school_id=user.school_id,
            actor_user_id=user.id,
            target_user_id=profile.id,
            action="account.status_changed",
            previous_status=previous_status,
            new_status=payload.account_status,
            description=payload.reason.strip(),
        )
    )
    await db.commit()
    return SuccessEnvelope(
        data=AccountUserRead(
            id=profile.id,
            full_name=profile.display_name,
            email=profile.email,
            phone_number=profile.phone,
            account_status=profile.account_status,
            roles=await _role_names(db, profile.id),
            permissions=await _permission_names(db, profile.id),
            created_at=profile.created_at,
        )
    )


@router.put("/users/{user_id}/permissions", response_model=SuccessEnvelope[list[str]])
async def replace_direct_permissions(
    user_id: UUID,
    payload: PermissionUpdate,
    user: Annotated[CurrentUser, Depends(require_super_admin)],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
) -> SuccessEnvelope[list[str]]:
    if user_id == user.id:
        raise APIError(
            status.HTTP_409_CONFLICT,
            "CANNOT_EDIT_SELF_PERMISSIONS",
            "The Super Admin cannot edit their own direct permissions.",
        )
    profile = await db.scalar(
        select(UserProfile).where(
            UserProfile.id == user_id, UserProfile.school_id == user.school_id
        )
    )
    if profile is None:
        raise APIError(status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND", "User not found.")
    permission_names = sorted(set(payload.permission_names))
    permissions = (
        (await db.scalars(select(Permission).where(Permission.name.in_(permission_names)))).all()
        if permission_names
        else []
    )
    if len(permissions) != len(permission_names):
        raise APIError(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "INVALID_PERMISSION",
            "One or more permissions are invalid.",
        )
    existing = (
        await db.scalars(select(UserPermission).where(UserPermission.user_id == user_id))
    ).all()
    for assignment in existing:
        await db.delete(assignment)
    db.add_all(
        [
            UserPermission(user_id=user_id, permission_id=permission.id, assigned_by=user.id)
            for permission in permissions
        ]
    )
    db.add(
        AccountAuditLog(
            school_id=user.school_id,
            actor_user_id=user.id,
            target_user_id=user_id,
            action="account.permissions_changed",
            previous_status=None,
            new_status=None,
            description=f"Replaced direct permissions ({len(permissions)} assigned).",
        )
    )
    await db.commit()
    return SuccessEnvelope(data=permission_names)


@router.get("/dashboard", response_model=SuccessEnvelope[ApprovalCounts])
async def approval_dashboard(
    user: Annotated[CurrentUser, Depends(require_super_admin)],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
) -> SuccessEnvelope[ApprovalCounts]:
    request_counts = (
        await db.execute(
            select(RegistrationRequest.requested_role, RegistrationRequest.status, func.count())
            .where(RegistrationRequest.school_id == user.school_id)
            .group_by(RegistrationRequest.requested_role, RegistrationRequest.status)
        )
    ).all()
    account_counts = (
        await db.execute(
            select(UserProfile.account_status, func.count())
            .where(UserProfile.school_id == user.school_id)
            .group_by(UserProfile.account_status)
        )
    ).all()
    requests = {(role, request_status): count for role, request_status, count in request_counts}
    accounts = {account_status: count for account_status, count in account_counts}
    return SuccessEnvelope(
        data=ApprovalCounts(
            total_requests=sum(count for _, _, count in request_counts),
            pending_admin_requests=requests.get(("admin", "pending"), 0),
            pending_staff_requests=requests.get(("staff", "pending"), 0),
            approved_accounts=accounts.get("approved", 0),
            rejected_requests=requests.get(("admin", "rejected"), 0)
            + requests.get(("staff", "rejected"), 0),
            suspended_accounts=accounts.get("suspended", 0),
        )
    )


@router.get("/audit-logs", response_model=SuccessEnvelope[list[AuditLogRead]])
async def list_account_audit_logs(
    user: Annotated[CurrentUser, Depends(require_super_admin)],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> SuccessEnvelope[list[AuditLogRead]]:
    records = (
        await db.scalars(
            select(AccountAuditLog)
            .where(AccountAuditLog.school_id == user.school_id)
            .order_by(AccountAuditLog.created_at.desc())
            .limit(limit)
        )
    ).all()
    return SuccessEnvelope(data=[AuditLogRead.model_validate(record) for record in records])


def _display_name(claims: dict[str, object], email: str) -> str:
    metadata = claims.get("user_metadata")
    if isinstance(metadata, dict):
        display_name = metadata.get("full_name")
        if isinstance(display_name, str) and display_name.strip():
            return display_name.strip()[:200]
    return email[:200]
