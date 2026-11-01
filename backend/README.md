# EduCore ERP backend

This repository starts the FastAPI backend for SIDDARDHA HIGH SCHOOL. The current implementation is the foundation and first delivery slice; it is **not** the complete ERP described by the product brief.

## Implemented

- FastAPI application with versioned OpenAPI, CORS allowlisting, health checks, and a consistent JSON success/error envelope.
- Async SQLAlchemy 2.x and Alembic with an initial PostgreSQL migration.
- Supabase asymmetric JWT verification through cached JWKS keys, including issuer, audience, expiration, subject, and OTP authentication-method checks.
- Database-backed school profiles, role/permission checks, tenant context, RLS policies, and audit records.
- Supabase OTP registration/login, backend-enforced account approval, one-time owner bootstrap, Super Admin account administration, and optional email notifications.
- Profile read/update and Super Admin-only Supabase Auth user provisioning.
- Student create/read/update/archive and paginated listing.
- Teacher create/list.
- Admission creation/listing and atomic conversion of approved applications into students.
- Transactional bulk attendance recording and date-based student history/summary.

## Not implemented yet

Examinations/results, assignments, fees/payments, library, transport/GPS, hostel, timetable, HR/payroll, messaging/notifications, reports/certificates, AI, Google Sheets, uploads/Storage, Realtime publication, backups, imports/exports, and complete resource-level parent/teacher access are not implemented. Their endpoints are intentionally not exposed as placeholders.

## Local setup

Use Python 3.12+, PostgreSQL 15+, and a Supabase project. Configure `.env` from `.env.example`. The database URL should use a restricted PostgreSQL application role; use a separate migration-owner URL for schema changes. The Supabase project must have asymmetric JWT signing keys and the matching issuer/JWKS URL.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

The API is served at `/api/v1`; Swagger UI is at `/docs`. `/api/v1/health` is liveness; `/api/v1/health/ready` checks PostgreSQL. Generate the frontend OpenAPI artifact with `python scripts/export_openapi.py`.

Before normal use, run `scripts/bootstrap.sql` as the database owner with the operator-selected school UUID. Set `SCHOOL_ID` and `SUPER_ADMIN_EMAIL` in the backend environment, then let that verified email claim the Super Admin account through `/owner-bootstrap`. The SQL script does not add or promote any user account.

## Database/RLS operating model

The application connection must be a non-owner, non-superuser role without `BYPASSRLS`. The request session sets transaction-local `app.user_id` and `app.school_id` only after verifying the Supabase JWT and resolving an active profile. Queries also scope by school in the service/API layer. Migrations must run through a separate schema-owner connection configured as `DATABASE_MIGRATION_URL`; never use that owner connection for API traffic.

See [deployment](docs/DEPLOYMENT.md), [authentication](docs/AUTHENTICATION.md), and [API contract](docs/API_CONTRACT.md) for integration details and current limitations.
