from math import ceil
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.permissions import require_permission
from app.db.session import get_scoped_db
from app.dependencies.auth import CurrentUser
from app.models.academics import Teacher
from app.models.operations import AuditLog
from app.schemas.academics import TeacherCreate, TeacherRead
from app.schemas.common import Page, SuccessEnvelope

router = APIRouter(prefix="/teachers", tags=["teachers"])


@router.get("", response_model=SuccessEnvelope[Page[TeacherRead]])
async def list_teachers(
    user: Annotated[CurrentUser, Depends(require_permission("teachers:read"))],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> SuccessEnvelope[Page[TeacherRead]]:
    total = (
        await db.scalar(
            select(func.count()).select_from(Teacher).where(Teacher.school_id == user.school_id)
        )
        or 0
    )
    result = await db.scalars(
        select(Teacher)
        .where(Teacher.school_id == user.school_id)
        .order_by(Teacher.last_name, Teacher.first_name)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return SuccessEnvelope(
        data=Page(
            items=[TeacherRead.model_validate(row) for row in result.all()],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size),
        )
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SuccessEnvelope[TeacherRead])
async def create_teacher(
    payload: TeacherCreate,
    user: Annotated[CurrentUser, Depends(require_permission("teachers:write"))],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
) -> SuccessEnvelope[TeacherRead]:
    teacher = Teacher(school_id=user.school_id, **payload.model_dump())
    db.add(teacher)
    await db.flush()
    db.add(
        AuditLog(
            school_id=user.school_id,
            actor_id=user.id,
            action="teacher.created",
            resource_type="teacher",
            resource_id=teacher.id,
        )
    )
    await db.commit()
    await db.refresh(teacher)
    return SuccessEnvelope(data=TeacherRead.model_validate(teacher), message="Teacher created")
