from datetime import date
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Timestamped, UUIDPrimaryKey


class Student(UUIDPrimaryKey, Timestamped, Base):
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint(
            "school_id", "admission_number", name="uq_students_school_admission_number"
        ),
        UniqueConstraint(
            "school_id", "class_name", "section", "roll_number", name="uq_students_roll_context"
        ),
        CheckConstraint(
            "status IN ('active', 'inactive', 'graduated', 'transferred')",
            name="ck_students_status",
        ),
    )

    school_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    admission_number: Mapped[str] = mapped_column(String(40), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    class_name: Mapped[str] = mapped_column(String(32), nullable=False)
    section: Mapped[str] = mapped_column(String(32), nullable=False)
    roll_number: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")


class Teacher(UUIDPrimaryKey, Timestamped, Base):
    __tablename__ = "teachers"
    __table_args__ = (
        UniqueConstraint("school_id", "employee_number", name="uq_teachers_school_employee_number"),
        CheckConstraint("status IN ('active', 'inactive', 'on_leave')", name="ck_teachers_status"),
    )

    school_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    employee_number: Mapped[str] = mapped_column(String(40), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")


class AdmissionApplication(UUIDPrimaryKey, Timestamped, Base):
    __tablename__ = "admission_applications"
    __table_args__ = (
        UniqueConstraint("school_id", "application_number", name="uq_admissions_school_number"),
        CheckConstraint(
            "status IN ('submitted', 'under_review', 'approved', 'rejected', 'converted')",
            name="ck_admissions_status",
        ),
    )

    school_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    application_number: Mapped[str] = mapped_column(String(40), nullable=False)
    applicant_name: Mapped[str] = mapped_column(String(200), nullable=False)
    requested_class: Mapped[str] = mapped_column(String(32), nullable=False)
    guardian_name: Mapped[str] = mapped_column(String(200), nullable=False)
    guardian_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="submitted")
    student_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("students.id", ondelete="SET NULL")
    )


class AttendanceRecord(UUIDPrimaryKey, Timestamped, Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "student_id",
            "attendance_date",
            "session",
            name="uq_attendance_student_date_session",
        ),
        CheckConstraint(
            "status IN ('present', 'absent', 'late', 'excused')",
            name="ck_attendance_status",
        ),
    )

    school_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    session: Mapped[str] = mapped_column(String(32), nullable=False, default="full_day")
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    remarks: Mapped[str | None] = mapped_column(String(500))
