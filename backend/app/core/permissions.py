from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.exceptions import APIError
from app.db.session import get_scoped_db
from app.dependencies.auth import CurrentUser, get_current_user
from app.models.identity import Permission, RolePermission, UserPermission, UserRole


def require_permission(permission_name: str) -> Callable[..., Awaitable[CurrentUser]]:
    async def check_permission(
        user: Annotated[CurrentUser, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_scoped_db)],
    ) -> CurrentUser:
        role_statement = (
            select(Permission.id)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(
                UserRole.user_id == user.id,
                UserRole.is_active.is_(True),
                Permission.name == permission_name,
            )
        )
        direct_statement = (
            select(UserPermission.id)
            .join(Permission, UserPermission.permission_id == Permission.id)
            .where(UserPermission.user_id == user.id, Permission.name == permission_name)
        )
        if await db.scalar(role_statement) is None and await db.scalar(direct_statement) is None:
            raise APIError(status.HTTP_403_FORBIDDEN, "PERMISSION_DENIED", "Permission denied")
        return user

    return check_permission
