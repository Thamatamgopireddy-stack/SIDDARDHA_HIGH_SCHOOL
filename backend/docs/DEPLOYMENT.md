# Deployment

## Configuration and prerequisites

Deploy Python 3.12+ with PostgreSQL 15+ (Supabase PostgreSQL is the production database). Set `APP_ENV=production`, `DEBUG=false`, and configure `DATABASE_URL`, `DATABASE_MIGRATION_URL`, `SUPABASE_URL`, `SUPABASE_JWT_ISSUER`, `SUPABASE_JWKS_URL`, `SUPER_ADMIN_EMAIL`, `SCHOOL_ID`, and exact `CORS_ORIGINS`. Never commit `.env` or expose `SUPABASE_SERVICE_ROLE_KEY` to a browser. Use HTTPS between the frontend and API.

Use two database roles/connections:

1. `DATABASE_MIGRATION_URL` is a schema-owner credential used only by Alembic during deployment.
2. `DATABASE_URL` is a non-owner application role with no superuser or `BYPASSRLS` privileges. Grant only required table/sequence privileges. Do not run request traffic with the migration credential.

Grant the runtime role `SELECT, INSERT, UPDATE, DELETE` on `user_profiles`, `user_roles`, `user_permissions`, `registration_requests`, `account_audit_logs`, `role_permissions`, `students`, `teachers`, `admission_applications`, `attendance_records`, and `audit_logs`; grant `SELECT` on `schools`, `roles`, and `permissions`, and `SELECT, UPDATE` on `system_settings` for the one-time bootstrap. It must not own these tables, create/alter schema, or bypass RLS. Review grants against actual deployed routes as modules are added.

After configuring a new environment, run `alembic upgrade head` with the migration-owner URL, then execute `scripts/bootstrap.sql` as the database owner with operator-chosen `school_id` and `school_name` values. Set the same UUID as `SCHOOL_ID`, and set the one exact `SUPER_ADMIN_EMAIL`. The owner then verifies that email with OTP through `/owner-bootstrap`. Verify that the application role is not the table owner and cannot bypass RLS.

## Container

Build from the `backend` directory:

```powershell
docker build -t educore-backend .
docker run --env-file .env -p 8000:8000 educore-backend
```

Configure the deployment platform's health check as `/api/v1/health/ready`. Run migrations as a release/deploy step, not concurrently from every web worker. Review generated OpenAPI at `/openapi.json` before frontend integration.

## Operational limits

Redis, workers, backups/restoration, rate limiting, payment webhooks, Storage buckets, Realtime policies, production monitoring, and Render deployment automation are not part of this initial delivery. Do not represent the backend as production-ready until those controls and the remaining modules are implemented and acceptance-tested.
