from datetime import date
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
from app.models.academics import AttendanceRecord, Student
from app.models.operations import AuditLog
from app.schemas.academics import AttendanceBulk, AttendanceRead
from app.schemas.common import SuccessEnvelope

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("/bulk", response_model=SuccessEnvelope[list[AttendanceRead]])
async def record_attendance(
    payload: AttendanceBulk,
    user: Annotated[CurrentUser, Depends(require_permission("attendance:write"))],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
) -> SuccessEnvelope[list[AttendanceRead]]:
    keys = [(item.student_id, item.attendance_date, item.session) for item in payload.records]
    if len(set(keys)) != len(keys):
        raise APIError(
            status.HTTP_409_CONFLICT,
            "DUPLICATE_ATTENDANCE_IN_REQUEST",
            "The request contains duplicate student/date/session records",
        )
    student_ids = {item.student_id for item in payload.records}
    existing_students = set(
        (
            await db.scalars(
                select(Student.id).where(
                    Student.school_id == user.school_id,
                    Student.id.in_(student_ids),
                    Student.status == "active",
                )
            )
        ).all()
    )
    if existing_students != student_ids:
        raise APIError(
            status.HTTP_404_NOT_FOUND,
            "STUDENT_NOT_FOUND",
            "One or more active students were not found in this school",
        )
    rows = [
        AttendanceRecord(school_id=user.school_id, **record.model_dump())
        for record in payload.records
    ]
    db.add_all(rows)
    await db.flush()
    db.add(
        AuditLog(
            school_id=user.school_id,
            actor_id=user.id,
            action="attendance.bulk_recorded",
            resource_type="attendance",
            resource_id=rows[0].id,
        )
    )
    await db.commit()
    return SuccessEnvelope(
        data=[AttendanceRead.model_validate(row) for row in rows],
        message="Attendance recorded",
    )


@router.get("/student/{student_id}", response_model=SuccessEnvelope[list[AttendanceRead]])
async def student_attendance(
    student_id: UUID,
    user: Annotated[CurrentUser, Depends(require_permission("attendance:read"))],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
    start_date: date | None = None,
    end_date: date | None = None,
) -> SuccessEnvelope[list[AttendanceRead]]:
    filters = [
        AttendanceRecord.student_id == student_id,
        AttendanceRecord.school_id == user.school_id,
    ]
    if start_date:
        filters.append(AttendanceRecord.attendance_date >= start_date)
    if end_date:
        filters.append(AttendanceRecord.attendance_date <= end_date)
    result = await db.scalars(
        select(AttendanceRecord)
        .where(*filters)
        .order_by(AttendanceRecord.attendance_date.desc())
        .limit(500)
    )
    return SuccessEnvelope(data=[AttendanceRead.model_validate(row) for row in result.all()])


@router.get("/summary", response_model=SuccessEnvelope[dict[str, int]])
async def attendance_summary(
    user: Annotated[CurrentUser, Depends(require_permission("attendance:read"))],
    db: Annotated[AsyncSession, Depends(get_scoped_db)],
    attendance_date: Annotated[date, Query(alias="date")],
) -> SuccessEnvelope[dict[str, int]]:
    result = await db.execute(
        select(AttendanceRecord.status, func.count(AttendanceRecord.id))
        .where(
            AttendanceRecord.school_id == user.school_id,
            AttendanceRecord.attendance_date == attendance_date,
        )
        .group_by(AttendanceRecord.status)
    )
    summary: dict[str, int] = {row[0]: row[1] for row in result.all()}
    return SuccessEnvelope(data=summary)
