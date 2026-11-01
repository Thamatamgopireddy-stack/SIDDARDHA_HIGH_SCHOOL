from fastapi import APIRouter

from app.api.v1.endpoints import (
    admissions,
    attendance,
    auth,
    health,
    registration,
    students,
    teachers,
)

router = APIRouter()
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(registration.router)
router.include_router(registration.auth_router)
router.include_router(students.router)
router.include_router(teachers.router)
router.include_router(admissions.router)
router.include_router(attendance.router)
