from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.security import HTTPAuthorizationCredentials

from app.core.config import Settings
from app.core.exceptions import APIError
from app.core.security import verified_claims


@pytest.mark.asyncio
async def test_verified_claims_accepts_valid_supabase_signature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    user_id = uuid4()
    token = jwt.encode(
        {
            "sub": str(user_id),
            "iss": "https://school.example/auth/v1",
            "aud": "authenticated",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
            "amr": [{"method": "otp", "timestamp": int(datetime.now(UTC).timestamp())}],
        },
        private_key,
        algorithm="ES256",
    )

    class FakeJwksClient:
        def get_signing_key_from_jwt(self, _: str) -> SimpleNamespace:
            return SimpleNamespace(key=public_key)

    monkeypatch.setattr("app.core.security._jwks_client", lambda _: FakeJwksClient())
    claims = await verified_claims(
        HTTPAuthorizationCredentials(scheme="Bearer", credentials=token),
        Settings(
            supabase_jwks_url="https://school.example/keys",
            supabase_jwt_issuer="https://school.example/auth/v1",
        ),
    )
    assert claims["sub"] == str(user_id)


@pytest.mark.asyncio
async def test_verified_claims_rejects_wrong_audience(monkeypatch: pytest.MonkeyPatch) -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "iss": "https://school.example/auth/v1",
            "aud": "not-authenticated",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        private_key,
        algorithm="ES256",
    )

    class FakeJwksClient:
        def get_signing_key_from_jwt(self, _: str) -> SimpleNamespace:
            return SimpleNamespace(key=private_key.public_key())

    monkeypatch.setattr("app.core.security._jwks_client", lambda _: FakeJwksClient())
    with pytest.raises(APIError) as error:
        await verified_claims(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=token),
            Settings(
                supabase_jwks_url="https://school.example/keys",
                supabase_jwt_issuer="https://school.example/auth/v1",
            ),
        )
    assert error.value.code == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_verified_claims_rejects_password_authentication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "iss": "https://school.example/auth/v1",
            "aud": "authenticated",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
            "amr": [{"method": "password", "timestamp": int(datetime.now(UTC).timestamp())}],
        },
        private_key,
        algorithm="ES256",
    )

    class FakeJwksClient:
        def get_signing_key_from_jwt(self, _: str) -> SimpleNamespace:
            return SimpleNamespace(key=private_key.public_key())

    monkeypatch.setattr("app.core.security._jwks_client", lambda _: FakeJwksClient())
    with pytest.raises(APIError) as error:
        await verified_claims(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=token),
            Settings(
                supabase_jwks_url="https://school.example/keys",
                supabase_jwt_issuer="https://school.example/auth/v1",
            ),
        )
    assert error.value.code == "OTP_AUTHENTICATION_REQUIRED"
