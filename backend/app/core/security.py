from functools import lru_cache
from typing import Annotated, Any, cast
from uuid import UUID

import anyio
import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient, PyJWKClientError
from starlette import status

from app.core.config import Settings, get_settings
from app.core.exceptions import APIError

bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache(maxsize=8)
def _jwks_client(url: str) -> PyJWKClient:
    return PyJWKClient(url, cache_keys=True, lifespan=300, timeout=5)


async def verified_claims(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise APIError(
            status.HTTP_401_UNAUTHORIZED, "AUTHENTICATION_REQUIRED", "Bearer token required"
        )
    if not settings.supabase_jwks_url or not settings.supabase_jwt_issuer:
        raise APIError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "AUTHENTICATION_NOT_CONFIGURED",
            "Supabase JWT verification is not configured",
        )
    try:
        signing_key = await anyio.to_thread.run_sync(
            _jwks_client(settings.supabase_jwks_url).get_signing_key_from_jwt,
            credentials.credentials,
        )
        claims = cast(
            dict[str, Any],
            jwt.decode(
                credentials.credentials,
                signing_key.key,
                algorithms=settings.supabase_jwt_algorithms,
                audience=settings.supabase_jwt_audience,
                issuer=settings.supabase_jwt_issuer,
                options={"require": ["exp", "iss", "aud", "sub"]},
            ),
        )
        UUID(claims["sub"])
        amr = claims.get("amr")
        if not isinstance(amr, list) or not any(
            isinstance(method, dict) and method.get("method") == "otp" for method in amr
        ):
            raise APIError(
                status.HTTP_401_UNAUTHORIZED,
                "OTP_AUTHENTICATION_REQUIRED",
                "Sign in with a one-time email code to access the ERP.",
            )
        return claims
    except PyJWKClientError as exc:
        raise APIError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "AUTHENTICATION_PROVIDER_UNAVAILABLE",
            "Unable to retrieve trusted signing keys",
        ) from exc
    except (jwt.PyJWTError, ValueError, TypeError, KeyError) as exc:
        raise APIError(
            status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", "Invalid or expired access token"
        ) from exc


def clear_jwks_cache() -> None:
    _jwks_client.cache_clear()
