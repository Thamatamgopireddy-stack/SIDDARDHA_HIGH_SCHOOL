from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.academics import AttendanceBulk, AttendanceItem, StudentCreate
from app.schemas.registration import AdminRegistration


def test_student_create_accepts_expected_contract() -> None:
    payload = StudentCreate(
        admission_number="ADM-1",
        first_name="Aarav",
        last_name="Kumar",
        class_name="5",
        section="A",
        roll_number="12",
    )
    assert payload.admission_number == "ADM-1"
    assert payload.date_of_birth is None


def test_attendance_rejects_unknown_status() -> None:
    with pytest.raises(ValidationError):
        AttendanceItem(
            student_id=uuid4(),
            attendance_date=date(2026, 11, 1),
            status="unknown",
        )


def test_attendance_bulk_rejects_empty_batch() -> None:
    with pytest.raises(ValidationError):
        AttendanceBulk(records=[])


def test_registration_cannot_supply_a_role_or_approval_state() -> None:
    with pytest.raises(ValidationError):
        AdminRegistration(
            full_name="School Admin",
            email="admin@example.com",
            phone_number="+911234567890",
            department="Administration",
            designation="Principal",
            role="super_admin",
            account_status="approved",
        )
