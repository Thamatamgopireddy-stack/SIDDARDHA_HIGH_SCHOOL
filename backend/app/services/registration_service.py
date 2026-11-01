import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.config import Settings
from app.core.exceptions import APIError
from app.integrations.supabase.admin import fetch_auth_user
from app.models.identity import RegistrationRequest, UserProfile
from app.models.operations import School
from app.schemas.registration import RegistrationBase, StaffRegistration

logger = logging.getLogger(__name__)


async def submit_registration(
    *,
    payload: RegistrationBase,
    role: str,
    user_id: UUID,
    db: AsyncSession,
    settings: Settings,
) -> RegistrationRequest:
    enabled = settings.registration_enabled and (
        settings.admin_registration_enabled
        if role == "admin"
        else settings.staff_registration_enabled
    )
    if not enabled:
        raise APIError(
            status.HTTP_403_FORBIDDEN, "REGISTRATION_CLOSED", "Registration is currently closed."
        )
    if not settings.school_id:
        raise APIError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "REGISTRATION_NOT_CONFIGURED",
            "School registration is not configured.",
        )
    try:
        school_id = UUID(settings.school_id)
    except ValueError as exc:
        raise APIError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "REGISTRATION_NOT_CONFIGURED",
            "School registration is not configured.",
        ) from exc

    email = str(payload.email).strip().casefold()
    if settings.super_admin_email and email == settings.super_admin_email:
        raise APIError(
            status.HTTP_409_CONFLICT,
            "OWNER_MUST_USE_BOOTSTRAP",
            "The configured owner must use the one-time Super Admin bootstrap flow.",
        )
    domain = email.rsplit("@", 1)[-1]
    allowed_domains = {item.casefold().lstrip("@") for item in settings.allowed_email_domains}
    if allowed_domains and domain not in allowed_domains:
        raise APIError(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "EMAIL_DOMAIN_NOT_ALLOWED",
            "Use an email address approved by the school.",
        )

    auth_user = await fetch_auth_user(user_id, settings)
    verified_email = auth_user.get("email")
    if auth_user.get("email_verified") is not True:
        raise APIError(
            status.HTTP_403_FORBIDDEN,
            "EMAIL_VERIFICATION_REQUIRED",
            "Verify your email address before submitting a registration request.",
        )
    if not isinstance(verified_email, str) or verified_email.casefold() != email:
        raise APIError(
            status.HTTP_403_FORBIDDEN,
            "VERIFIED_EMAIL_MISMATCH",
            "The verified account email does not match the registration email.",
        )

    await db.execute(
        text("SELECT set_config('app.user_id', :user_id, true)"), {"user_id": str(user_id)}
    )
    await db.execute(
        text("SELECT set_config('app.school_id', :school_id, true)"),
        {"school_id": str(school_id)},
    )
    school = await db.get(School, school_id)
    if school is None or not school.is_active:
        raise APIError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "SCHOOL_NOT_CONFIGURED",
            "School registration is not available.",
        )

    profile = await db.get(UserProfile, user_id)
    if profile is not None and profile.account_status not in {
        "rejected",
        "pending_email_verification",
    }:
        raise APIError(
            status.HTTP_409_CONFLICT,
            "ACCOUNT_ALREADY_REGISTERED",
            "An account or registration request already exists for this email.",
        )
    pending = await db.scalar(
        select(RegistrationRequest.id).where(
            RegistrationRequest.school_id == school_id,
            func.lower(RegistrationRequest.email) == email,
            RegistrationRequest.status == "pending",
        )
    )
    if pending is not None:
        raise APIError(
            status.HTTP_409_CONFLICT,
            "REGISTRATION_ALREADY_PENDING",
            "A registration request is already waiting for review.",
        )
    cutoff = datetime.now(UTC) - timedelta(hours=1)
    recent_count = await db.scalar(
        select(func.count(RegistrationRequest.id)).where(
            RegistrationRequest.applicant_user_id == user_id,
            RegistrationRequest.created_at >= cutoff,
        )
    )
    if (recent_count or 0) >= 3:
        raise APIError(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "REGISTRATION_RATE_LIMITED",
            "Too many registration attempts. Try again later.",
        )

    if profile is None:
        profile = UserProfile(
            id=user_id,
            school_id=school_id,
            display_name=payload.full_name.strip(),
            email=email,
            phone=payload.phone_number.strip(),
            employee_id=payload.employee_id,
            department=payload.department.strip(),
            designation=payload.designation.strip(),
            staff_category=_staff_category(payload),
            account_status="pending",
            email_verified=True,
            is_active=False,
        )
        db.add(profile)
        await db.flush()
    else:
        profile.display_name = payload.full_name.strip()
        profile.email = email
        profile.phone = payload.phone_number.strip()
        profile.employee_id = payload.employee_id
        profile.department = payload.department.strip()
        profile.designation = payload.designation.strip()
        profile.staff_category = _staff_category(payload)
        profile.account_status = "pending"
        profile.email_verified = True
        profile.is_active = False

    request = RegistrationRequest(
        school_id=school_id,
        applicant_user_id=user_id,
        full_name=payload.full_name.strip(),
        email=email,
        phone_number=payload.phone_number.strip(),
        employee_id=payload.employee_id,
        department=payload.department.strip(),
        designation=payload.designation.strip(),
        staff_category=_staff_category(payload),
        requested_role=role,
        email_verified=True,
        status="pending",
    )
    db.add(request)
    logger.info("Verified registration request submitted", extra={"requested_role": role})
    return request


def _staff_category(payload: RegistrationBase) -> str | None:
    if isinstance(payload, StaffRegistration):
        return payload.staff_category.strip()
    return None
