from functools import lru_cache
from typing import Annotated
from uuid import UUID

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "EduCore ERP"
    school_name: str = "SIDDARDHA HIGH SCHOOL"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    database_url: str = ""
    database_migration_url: str = ""
    database_pool_size: int = 10
    database_max_overflow: int = 20
    supabase_url: str = ""
    supabase_anon_key: SecretStr | None = None
    supabase_service_role_key: SecretStr | None = None
    supabase_jwt_issuer: str = ""
    supabase_jwks_url: str = ""
    supabase_jwt_algorithms: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["ES256", "RS256"]
    )
    supabase_jwt_audience: str = "authenticated"
    super_admin_email: str = ""
    school_id: str = ""
    allowed_email_domains: Annotated[list[str], NoDecode] = Field(default_factory=list)
    registration_enabled: bool = True
    staff_registration_enabled: bool = True
    admin_registration_enabled: bool = True
    email_provider_api_key: SecretStr | None = None
    email_from_address: str = ""
    frontend_url: str = "http://localhost:5173"
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )
    redis_url: str = ""
    ai_provider: str = ""
    ai_api_key: SecretStr | None = None
    ai_model: str = ""
    google_service_account_json: SecretStr | None = None
    google_sheets_enabled: bool = False
    payment_gateway: str = ""
    payment_gateway_secret: SecretStr | None = None
    log_level: str = "INFO"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> str | list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}:
            raise ValueError("LOG_LEVEL must be a standard Python logging level")
        return normalized

    @field_validator("supabase_jwt_algorithms", mode="before")
    @classmethod
    def parse_jwt_algorithms(cls, value: str | list[str]) -> str | list[str]:
        if isinstance(value, str):
            return [algorithm.strip() for algorithm in value.split(",") if algorithm.strip()]
        return value

    @field_validator("supabase_jwt_algorithms")
    @classmethod
    def validate_jwt_algorithms(cls, value: list[str]) -> list[str]:
        supported = {"ES256", "RS256"}
        if not value or not set(value).issubset(supported):
            raise ValueError("SUPABASE_JWT_ALGORITHMS may contain only ES256 and RS256")
        return value

    @field_validator("allowed_email_domains", mode="before")
    @classmethod
    def parse_email_domains(cls, value: str | list[str]) -> str | list[str]:
        if isinstance(value, str):
            return [
                domain.strip().lower().lstrip("@") for domain in value.split(",") if domain.strip()
            ]
        return value

    @field_validator("super_admin_email")
    @classmethod
    def normalize_super_admin_email(cls, value: str) -> str:
        return value.strip().casefold()

    @field_validator("school_id")
    @classmethod
    def validate_school_id(cls, value: str) -> str:
        normalized = value.strip()
        if normalized:
            UUID(normalized)
        return normalized

    def validate_production(self) -> None:
        if self.app_env.lower() == "production":
            required = {
                "DATABASE_URL": self.database_url,
                "DATABASE_MIGRATION_URL": self.database_migration_url,
                "SUPABASE_URL": self.supabase_url,
                "SUPABASE_JWT_ISSUER": self.supabase_jwt_issuer,
                "SUPABASE_JWKS_URL": self.supabase_jwks_url,
                "SUPABASE_SERVICE_ROLE_KEY": (
                    self.supabase_service_role_key.get_secret_value()
                    if self.supabase_service_role_key
                    else ""
                ),
                "SUPER_ADMIN_EMAIL": self.super_admin_email,
                "SCHOOL_ID": self.school_id,
            }
            missing = [key for key, value in required.items() if not value]
            if missing:
                raise ValueError(f"Missing required production configuration: {', '.join(missing)}")
            if self.debug:
                raise ValueError("DEBUG must be false in production")
            if "*" in self.cors_origins:
                raise ValueError("Wildcard CORS origins are not allowed in production")
            if not self.supabase_url.startswith(
                "https://"
            ) or not self.supabase_jwks_url.startswith("https://"):
                raise ValueError("Supabase endpoints must use HTTPS in production")
            if (
                self.email_provider_api_key
                and self.email_provider_api_key.get_secret_value().strip()
                and not self.email_from_address.strip()
            ):
                raise ValueError(
                    "EMAIL_FROM_ADDRESS is required when email notifications are enabled"
                )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_production()
    return settings
