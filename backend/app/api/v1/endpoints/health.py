from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.config import Settings, get_settings
from app.core.exceptions import APIError
from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, object]:
    return {
        "success": True,
        "data": {"status": "ok", "app": settings.app_name, "environment": settings.app_env},
        "message": "Service is healthy",
        "meta": None,
    }


@router.get("/health/ready")
async def readiness(db: Annotated[AsyncSession, Depends(get_db)]) -> dict[str, object]:
    try:
        await db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise APIError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "DATABASE_UNAVAILABLE",
            "Database readiness check failed",
        ) from exc
    return {
        "success": True,
        "data": {"status": "ready", "database": "connected"},
        "message": "Service is ready",
        "meta": None,
    }
