from uuid import UUID

import httpx
from starlette import status

from app.core.config import Settings
from app.core.exceptions import APIError


async def fetch_auth_user(user_id: UUID, settings: Settings) -> dict[str, object]:
    if (
        not settings.supabase_url
        or settings.supabase_service_role_key is None
        or not settings.supabase_service_role_key.get_secret_value().strip()
    ):
        raise APIError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "SUPABASE_ADMIN_NOT_CONFIGURED",
            "Supabase Auth profile provisioning is not configured",
        )
    service_key = settings.supabase_service_role_key.get_secret_value()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{settings.supabase_url.rstrip('/')}/auth/v1/admin/users/{user_id}",
                headers={"apikey": service_key, "Authorization": f"Bearer {service_key}"},
            )
    except httpx.HTTPError as exc:
        raise APIError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "SUPABASE_AUTH_UNAVAILABLE",
            "Supabase Auth is temporarily unavailable",
        ) from exc
    if response.status_code == status.HTTP_404_NOT_FOUND:
        raise APIError(
            status.HTTP_404_NOT_FOUND, "AUTH_USER_NOT_FOUND", "Supabase Auth user not found"
        )
    if response.status_code != status.HTTP_200_OK:
        raise APIError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "SUPABASE_AUTH_ERROR",
            "Supabase Auth rejected the profile lookup",
        )
    try:
        result = response.json()
    except ValueError as exc:
        raise APIError(
            status.HTTP_502_BAD_GATEWAY,
            "SUPABASE_AUTH_RESPONSE_INVALID",
            "Supabase Auth returned an invalid user profile",
        ) from exc
    if not isinstance(result, dict) or result.get("id") != str(user_id):
        raise APIError(
            status.HTTP_502_BAD_GATEWAY,
            "SUPABASE_AUTH_RESPONSE_INVALID",
            "Supabase Auth returned an invalid user profile",
        )
    email = result.get("email")
    confirmed_at = result.get("email_confirmed_at")
    return {
        "email": email if isinstance(email, str) else None,
        "email_verified": isinstance(confirmed_at, str) and bool(confirmed_at),
    }
