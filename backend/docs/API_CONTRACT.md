# EduCore API contract

Base path: `/api/v1`. The machine-readable OpenAPI contract is generated at [`openapi.json`](./openapi.json) from the running application.

## Conventions

- JSON field names are `snake_case`; IDs are UUIDs; dates use ISO 8601.
- Successful responses use `{ "success": true, "data": ..., "message": "...", "meta": null }`.
- Errors use `{ "success": false, "error": { "code": "...", "message": "...", "details": {} } }`.
- Paginated collections put `items`, `page`, `page_size`, `total`, and `total_pages` inside `data`.
- List page sizes default to 20 and are capped at 100.
- Authenticate protected routes with `Authorization: Bearer <Supabase access token>`.

## Currently implemented routes

| Method | Path | Permission |
|---|---|---|
| GET | `/health` | Public liveness |
| GET | `/health/ready` | Public readiness |
| GET | `/auth/status` | Verified email OTP session |
| POST | `/auth/bootstrap-super-admin` | Verified configured owner email, one-time |
| GET | `/auth/me` | Approved account |
| GET | `/auth/permissions` | Approved account |
| PATCH | `/auth/profile` | Approved account, self |
| POST | `/auth/provision-profile` | Super Admin |
| POST | `/registration/admin` | Verified OTP email, admin registration enabled |
| POST | `/registration/staff` | Verified OTP email, staff registration enabled |
| GET | `/registration/requests` | Super Admin |
| POST | `/registration/requests/{request_id}/approve` | Super Admin |
| POST | `/registration/requests/{request_id}/reject` | Super Admin |
| GET | `/registration/users` | Super Admin |
| PATCH | `/registration/users/{user_id}/status` | Super Admin |
| PUT | `/registration/users/{user_id}/permissions` | Super Admin |
| GET | `/registration/dashboard` | Super Admin |
| GET | `/registration/audit-logs` | Super Admin |
| GET/POST | `/students` | `students:read` / `students:write` |
| GET/PATCH/DELETE | `/students/{student_id}` | `students:read` / `students:write` |
| GET/POST | `/teachers` | `teachers:read` / `teachers:write` |
| GET/POST | `/admissions` | `admissions:read` / `admissions:write` |
| PATCH | `/admissions/{application_id}` | `admissions:approve` |
| POST | `/admissions/{application_id}/convert-to-student` | `admissions:approve` |
| POST | `/attendance/bulk` | `attendance:write` |
| GET | `/attendance/student/{student_id}` | `attendance:read` |
| GET | `/attendance/summary?date=YYYY-MM-DD` | `attendance:read` |

`DELETE /students/{student_id}` is a soft archive and returns the archived student. Attendance bulk requests are atomic and reject duplicate keys within a request; database uniqueness prevents duplicate student/date/session records.

All authenticated API endpoints require a Supabase JWT whose `amr` claim includes `otp`; password-authenticated tokens are rejected. Registration/decision responses include `meta.email_notification` with `sent`, `not_configured`, or `failed`. OTP delivery itself is handled by Supabase Auth and its configured provider rate limits.

The route catalog in the product brief is a target contract, not a claim that unlisted modules exist. Implementations and additional routes must be added to the generated OpenAPI spec before frontend integration.
