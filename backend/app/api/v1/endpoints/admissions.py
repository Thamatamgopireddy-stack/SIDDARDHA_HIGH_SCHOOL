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
from app.models.academics import AdmissionApplication, Student
from app.models.operations import AuditLog
from app.schemas.academics import (
    AdmissionCreate,
    AdmissionDecision,
    AdmissionRead,
    StudentCreate,
    StudentRead,
)
from app.schemas.common import Page, SuccessEnvelope

router = APIRouter(prefix="/admissions", tags=["admissions"])


@router.get("", response_model=SuccessEnvelope[Page[AdmissionRead]])
async def list_admissions(
    user: Annotated[CurrentUser, Depends(require_permission("admissions:read"))],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    admission_status: str | None = Query(default=None, alias="status"),
) -> SuccessEnvelope[Page[AdmissionRead]]:
    filters = [AdmissionApplication.school_id == user.school_id]
    if admission_status:
        filters.append(AdmissionApplication.status == admission_status)
    total = (
        await db.scalar(select(func.count()).select_from(AdmissionApplication).where(*filters)) or 0
    )
    result = await db.scalars(
        select(AdmissionApplication)
        .where(*filters)
        .order_by(AdmissionApplication.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return SuccessEnvelope(
        data=Page(
            items=[AdmissionRead.model_validate(row) for row in result.all()],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size),
        )
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SuccessEnvelope[AdmissionRead])
async def create_admission(
    payload: AdmissionCreate,
    user: Annotated[CurrentUser, Depends(require_permission("admissions:write"))],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
) -> SuccessEnvelope[AdmissionRead]:
    application = AdmissionApplication(school_id=user.school_id, **payload.model_dump())
    db.add(application)
    await db.flush()
    db.add(
        AuditLog(
            school_id=user.school_id,
            actor_id=user.id,
            action="admission.submitted",
            resource_type="admission_application",
            resource_id=application.id,
        )
    )
    await db.commit()
    await db.refresh(application)
    return SuccessEnvelope(
        data=AdmissionRead.model_validate(application), message="Application created"
    )


@router.patch("/{application_id}", response_model=SuccessEnvelope[AdmissionRead])
async def decide_admission(
    application_id: UUID,
    payload: AdmissionDecision,
    user: Annotated[CurrentUser, Depends(require_permission("admissions:approve"))],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
) -> SuccessEnvelope[AdmissionRead]:
    application = await db.scalar(
        select(AdmissionApplication)
        .where(
            AdmissionApplication.id == application_id,
            AdmissionApplication.school_id == user.school_id,
        )
        .with_for_update()
    )
    if application is None:
        raise APIError(status.HTTP_404_NOT_FOUND, "ADMISSION_NOT_FOUND", "Application not found")
    if application.status not in {"submitted", "under_review"}:
        raise APIError(
            status.HTTP_409_CONFLICT,
            "ADMISSION_STATE_CONFLICT",
            "This application has already been decided",
        )
    application.status = payload.status
    db.add(
        AuditLog(
            school_id=user.school_id,
            actor_id=user.id,
            action=f"admission.{payload.status}",
            resource_type="admission_application",
            resource_id=application.id,
        )
    )
    await db.commit()
    await db.refresh(application)
    return SuccessEnvelope(
        data=AdmissionRead.model_validate(application), message="Application updated"
    )


@router.post(
    "/{application_id}/convert-to-student",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessEnvelope[StudentRead],
)
async def convert_admission(
    application_id: UUID,
    payload: StudentCreate,
    user: Annotated[CurrentUser, Depends(require_permission("admissions:approve"))],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
) -> SuccessEnvelope[StudentRead]:
    application = await db.scalar(
        select(AdmissionApplication)
        .where(
            AdmissionApplication.id == application_id,
            AdmissionApplication.school_id == user.school_id,
        )
        .with_for_update()
    )
    if application is None:
        raise APIError(status.HTTP_404_NOT_FOUND, "ADMISSION_NOT_FOUND", "Application not found")
    if application.status != "approved":
        raise APIError(
            status.HTTP_409_CONFLICT,
            "ADMISSION_NOT_APPROVED",
            "Only approved applications can be converted",
        )
    if payload.class_name != application.requested_class:
        raise APIError(
            status.HTTP_409_CONFLICT,
            "ADMISSION_CLASS_MISMATCH",
            "The student's class must match the approved requested class",
        )
    student = Student(school_id=user.school_id, **payload.model_dump())
    db.add(student)
    await db.flush()
    application.status = "converted"
    application.student_id = student.id
    db.add(
        AuditLog(
            school_id=user.school_id,
            actor_id=user.id,
            action="admission.converted",
            resource_type="admission_application",
            resource_id=application.id,
        )
    )
    await db.commit()
    await db.refresh(student)
    return SuccessEnvelope(data=StudentRead.model_validate(student), message="Admission converted")
