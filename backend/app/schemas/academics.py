from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StudentCreate(BaseModel):
    admission_number: str = Field(min_length=1, max_length=40)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date | None = None
    class_name: str = Field(min_length=1, max_length=32)
    section: str = Field(min_length=1, max_length=32)
    roll_number: str = Field(min_length=1, max_length=32)


class StudentUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    class_name: str | None = Field(default=None, min_length=1, max_length=32)
    section: str | None = Field(default=None, min_length=1, max_length=32)
    roll_number: str | None = Field(default=None, min_length=1, max_length=32)
    status: str | None = Field(default=None, pattern="^(active|inactive|graduated|transferred)$")

    @model_validator(mode="after")
    def reject_explicit_nulls(self) -> "StudentUpdate":
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Student fields cannot be set to null")
        return self


class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    admission_number: str
    first_name: str
    last_name: str
    date_of_birth: date | None
    class_name: str
    section: str
    roll_number: str
    status: str
    created_at: datetime
    updated_at: datetime


class TeacherCreate(BaseModel):
    employee_number: str = Field(min_length=1, max_length=40)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=32)


class TeacherRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_number: str
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class AdmissionCreate(BaseModel):
    application_number: str = Field(min_length=1, max_length=40)
    applicant_name: str = Field(min_length=1, max_length=200)
    requested_class: str = Field(min_length=1, max_length=32)
    guardian_name: str = Field(min_length=1, max_length=200)
    guardian_phone: str = Field(min_length=1, max_length=32)


class AdmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_number: str
    applicant_name: str
    requested_class: str
    guardian_name: str
    guardian_phone: str
    status: str
    created_at: datetime
    updated_at: datetime


class AdmissionDecision(BaseModel):
    status: str = Field(pattern="^(under_review|approved|rejected)$")


class AttendanceItem(BaseModel):
    student_id: UUID
    attendance_date: date
    session: str = Field(default="full_day", min_length=1, max_length=32)
    status: str = Field(pattern="^(present|absent|late|excused)$")
    remarks: str | None = Field(default=None, max_length=500)


class AttendanceBulk(BaseModel):
    records: list[AttendanceItem] = Field(min_length=1, max_length=500)


class AttendanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    attendance_date: date
    session: str
    status: str
    remarks: str | None
