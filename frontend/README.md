# EduCore ERP frontend

The React 18 + TypeScript frontend integrates with Supabase Auth for identity and the FastAPI backend for school data.

## Current working scope

The UI follows the backend contract in `../backend/docs/API_CONTRACT.md`. It currently supports:

- Supabase email/password sign-in, persistent/refreshable sessions, password reset and password update.
- Profile display/update and backend-provided permission checks.
- Dashboard counts sourced from allowed backend list/summary APIs and live API/database health checks.
- Student search, pagination, create, profile view, edit, soft archive and recent attendance history.
- Teacher listing, search and create.
- Admission creation, status review/approval/rejection, and approved application conversion.
- Attendance class register, daily summary, duplicate-aware register display and bulk submit.

Other product-brief modules are intentionally not shown as fake pages because those API operations are not yet present in the backend contract. Uploads, realtime events and PWA/offline functionality are not claimed as implemented.

## Setup

Use Node.js 20+ and npm. Set up the Python backend separately; see `../backend/README.md`.

```powershell
cd frontend
npm.cmd install
Copy-Item .env.example .env
notepad .env
npm.cmd run dev
```

Set `VITE_API_BASE_URL` to the FastAPI `/api/v1` base URL, `VITE_SUPABASE_URL` to the project URL, and `VITE_SUPABASE_ANON_KEY` to the public anon key. These values are browser-visible. **Never add a Supabase service-role key or other secret to a Vite variable.** Restart Vite after editing `.env`.

Open the Vite URL (normally `http://localhost:5173`). Configure the Supabase Auth redirect allowlist to include `http://localhost:5173/reset-password` for password reset.

## Validation

```powershell
npm.cmd run test
npm.cmd run lint
npm.cmd run build
```

The user must have an active backend profile and the permissions required by each route. Successful Supabase sign-in alone does not grant application access.
