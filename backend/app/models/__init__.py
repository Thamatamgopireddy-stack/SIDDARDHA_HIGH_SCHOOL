from app.models.academics import AdmissionApplication, AttendanceRecord, Student, Teacher
from app.models.identity import (
    AccountAuditLog,
    Permission,
    RegistrationRequest,
    Role,
    RolePermission,
    SystemSetting,
    UserPermission,
    UserProfile,
    UserRole,
)
from app.models.operations import AuditLog, School

__all__ = [
    "AdmissionApplication",
    "AccountAuditLog",
    "AttendanceRecord",
    "AuditLog",
    "Permission",
    "Role",
    "RolePermission",
    "RegistrationRequest",
    "School",
    "Student",
    "SystemSetting",
    "Teacher",
    "UserPermission",
    "UserProfile",
    "UserRole",
]
