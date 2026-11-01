import pytest

from app.core.config import Settings


def test_comma_separated_origins_and_algorithms_are_parsed() -> None:
    settings = Settings(
        _env_file=None,
        cors_origins="https://frontend.example,http://localhost:5173",
        supabase_jwt_algorithms="ES256,RS256",
    )
    assert settings.cors_origins == ["https://frontend.example", "http://localhost:5173"]
    assert settings.supabase_jwt_algorithms == ["ES256", "RS256"]


def test_production_requires_migration_credentials() -> None:
    settings = Settings(_env_file=None, app_env="production")
    with pytest.raises(ValueError, match="DATABASE_MIGRATION_URL"):
        settings.validate_production()


def test_school_id_must_be_a_uuid_when_configured() -> None:
    with pytest.raises(ValueError):
        Settings(_env_file=None, school_id="not-a-uuid")
