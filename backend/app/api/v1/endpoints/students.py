from math import ceil
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.exceptions import APIError
from app.core.permissions import require_permission
from app.db.session import get_scoped_db
from app.dependencies.auth import CurrentUser
from app.models.academics import Student
from app.models.operations import AuditLog
from app.schemas.academics import StudentCreate, StudentRead, StudentUpdate
from app.schemas.common import Page, SuccessEnvelope

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=SuccessEnvelope[Page[StudentRead]])
async def list_students(
    user: Annotated[CurrentUser, Depends(require_permission("students:read"))],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    class_name: str | None = None,
    section: str | None = None,
    search: str | None = Query(default=None, max_length=100),
) -> SuccessEnvelope[Page[StudentRead]]:
    filters = [Student.school_id == user.school_id]
    if class_name:
        filters.append(Student.class_name == class_name)
    if section:
        filters.append(Student.section == section)
    if search:
        filters.append(
            (Student.first_name.ilike(f"%{search}%"))
            | (Student.last_name.ilike(f"%{search}%"))
            | (Student.admission_number.ilike(f"%{search}%"))
        )
    total = await db.scalar(select(func.count()).select_from(Student).where(*filters)) or 0
    statement = (
        select(Student)
        .where(*filters)
        .order_by(Student.class_name, Student.section, Student.roll_number)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list((await db.scalars(statement)).all())
    return SuccessEnvelope(
        data=Page(
            items=[StudentRead.model_validate(item) for item in items],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size),
        )
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SuccessEnvelope[StudentRead])
async def create_student(
    payload: StudentCreate,
    user: Annotated[CurrentUser, Depends(require_permission("students:write"))],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
) -> SuccessEnvelope[StudentRead]:
    student = Student(school_id=user.school_id, **payload.model_dump())
    db.add(student)
    await db.flush()
    db.add(
        AuditLog(
            school_id=user.school_id,
            actor_id=user.id,
            action="student.created",
            resource_type="student",
            resource_id=student.id,
        )
    )
    await db.commit()
    await db.refresh(student)
    return SuccessEnvelope(data=StudentRead.model_validate(student), message="Student created")


@router.get("/{student_id}", response_model=SuccessEnvelope[StudentRead])
async def read_student(
    student_id: UUID,
    user: Annotated[CurrentUser, Depends(require_permission("students:read"))],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
) -> SuccessEnvelope[StudentRead]:
    student = await db.scalar(
        select(Student).where(Student.id == student_id, Student.school_id == user.school_id)
    )
    if student is None:
        raise APIError(status.HTTP_404_NOT_FOUND, "STUDENT_NOT_FOUND", "Student not found")
    return SuccessEnvelope(data=StudentRead.model_validate(student))


@router.patch("/{student_id}", response_model=SuccessEnvelope[StudentRead])
async def update_student(
    student_id: UUID,
    payload: StudentUpdate,
    user: Annotated[CurrentUser, Depends(require_permission("students:write"))],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
) -> SuccessEnvelope[StudentRead]:
    student = await db.scalar(
        select(Student).where(Student.id == student_id, Student.school_id == user.school_id)
    )
    if student is None:
        raise APIError(status.HTTP_404_NOT_FOUND, "STUDENT_NOT_FOUND", "Student not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    db.add(
        AuditLog(
            school_id=user.school_id,
            actor_id=user.id,
            action="student.updated",
            resource_type="student",
            resource_id=student.id,
        )
    )
    await db.commit()
    await db.refresh(student)
    return SuccessEnvelope(data=StudentRead.model_validate(student), message="Student updated")


@router.delete("/{student_id}", response_model=SuccessEnvelope[StudentRead])
async def archive_student(
    student_id: UUID,
    user: Annotated[CurrentUser, Depends(require_permission("students:write"))],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
) -> SuccessEnvelope[StudentRead]:
    student = await db.scalar(
        select(Student).where(Student.id == student_id, Student.school_id == user.school_id)
    )
    if student is None:
        raise APIError(status.HTTP_404_NOT_FOUND, "STUDENT_NOT_FOUND", "Student not found")
    student.status = "inactive"
    db.add(
        AuditLog(
            school_id=user.school_id,
            actor_id=user.id,
            action="student.archived",
            resource_type="student",
            resource_id=student.id,
        )
    )
    await db.commit()
    await db.refresh(student)
    return SuccessEnvelope(data=StudentRead.model_validate(student), message="Student archived")
