from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from starlette import status

from app.core.config import Settings, get_settings
from app.core.exceptions import APIError
from app.core.security import verified_claims
from app.models.identity import UserProfile


def _database_url(settings: Settings) -> str:
    url = settings.database_url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def create_session_factory(settings: Settings) -> async_sessionmaker[AsyncSession] | None:
    url = _database_url(settings)
    if not url:
        return None
    return _cached_session_factory(url, settings.database_pool_size, settings.database_max_overflow)


@lru_cache(maxsize=8)
def _cached_session_factory(
    url: str, pool_size: int, max_overflow: int
) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(
        url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
    )
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_db(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncIterator[AsyncSession]:
    factory = create_session_factory(settings)
    if factory is None:
        raise APIError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "DATABASE_NOT_CONFIGURED",
            "Database connection is not configured",
        )
    async with factory() as session:
        yield session


async def get_scoped_db(
    db: Annotated[AsyncSession, Depends(get_db)],
    claims: Annotated[dict[str, object], Depends(verified_claims)],
) -> AsyncIterator[AsyncSession]:
    user_id = UUID(str(claims["sub"]))
    await db.execute(
        text("SELECT set_config('app.user_id', :user_id, true)"),
        {"user_id": str(user_id)},
    )
    profile = await db.scalar(select(UserProfile).where(UserProfile.id == user_id))
    if profile is None:
        raise APIError(
            status.HTTP_403_FORBIDDEN, "PROFILE_UNAVAILABLE", "User profile is unavailable"
        )
    await db.execute(
        text("SELECT set_config('app.school_id', :school_id, true)"),
        {"school_id": str(profile.school_id)},
    )
    from app.models.identity import Role, UserRole

    role_names = (
        await db.scalars(
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id, UserRole.is_active.is_(True))
        )
    ).all()
    await db.execute(
        text("SELECT set_config('app.is_super_admin', :is_super_admin, true)"),
        {"is_super_admin": str("super_admin" in role_names).lower()},
    )
    yield db
