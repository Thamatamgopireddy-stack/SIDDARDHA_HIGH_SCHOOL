# Authentication and authorization

Supabase Auth is the identity provider. The frontend requests and verifies email OTPs through Supabase Auth; it must not send passwords to this API. FastAPI verifies asymmetric JWT signatures against the configured JWKS URL and validates issuer, audience, expiration, UUID subject, and an `amr` claim containing `otp`. This rejects password-authenticated JWTs even if a caller bypasses the frontend. PyJWT's JWKS client caches keys and refreshes them on key rotation.

After JWT verification, the API resolves `user_profiles.id` to the Supabase Auth subject and rejects profiles that are unverified, pending, rejected, suspended, disabled, or inactive before any ERP route is available. `GET /api/v1/auth/status` is the limited authenticated status path for those accounts. A verified user submits either an admin or staff request; role and approval status are derived only by the API. Only the Super Admin can approve/reject applications or administer accounts and direct permissions.

First-time setup: enable email OTP in Supabase Auth and configure its email template to include `{{ .Token }}` (not only a magic-link URL). Run migrations, execute `scripts/bootstrap.sql` with the database-owner connection to create the school and seed baseline permissions/roles, set the matching `SCHOOL_ID` and verified `SUPER_ADMIN_EMAIL` in the backend environment, and visit `/owner-bootstrap` in the frontend. The endpoint checks the verified Auth email, school, and a locked one-time database setting before assigning Super Admin. Never insert an arbitrary user into `user_profiles` as an administrator. The backend-only Supabase service-role key is required to verify Auth user email status and must never be exposed to the browser.

OTP email messages and rate limits are controlled by Supabase Auth. Optional account-approval notifications use the configured Resend API key and sender; API responses explicitly report `email_notification` as `sent`, `not_configured`, or `failed`.

## Current boundaries

This delivery does not yet implement parent-child links, teacher-class authorization, Supabase session revocation, per-resource field filtering, realtime approval updates, or every role described in the product brief. The approval UI refreshes its queue by polling; it does not rely on Supabase Realtime. Until remaining workflows exist, do not grant broad read permissions to parent/student accounts or expose this API to production users.
