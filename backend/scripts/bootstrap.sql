\set ON_ERROR_STOP on

-- Run as the database owner after migrations:
-- psql "$DATABASE_MIGRATION_URL" -v school_id='...' -v school_name='SIDDARDHA HIGH SCHOOL' -f scripts/bootstrap.sql
-- Then set SCHOOL_ID to the same UUID and claim Super Admin through the verified owner login.
BEGIN;

INSERT INTO schools (id, name, timezone, currency, is_active)
VALUES (:'school_id'::uuid, :'school_name', 'Asia/Kolkata', 'INR', true)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, is_active = true;

INSERT INTO permissions (id, name, description)
VALUES
    (gen_random_uuid(), 'users:manage', 'Provision school user profiles'),
    (gen_random_uuid(), 'students:read', 'Read student records'),
    (gen_random_uuid(), 'students:write', 'Manage student records'),
    (gen_random_uuid(), 'teachers:read', 'Read teacher records'),
    (gen_random_uuid(), 'teachers:write', 'Manage teacher records'),
    (gen_random_uuid(), 'admissions:read', 'Read admission applications'),
    (gen_random_uuid(), 'admissions:write', 'Create admission applications'),
    (gen_random_uuid(), 'admissions:approve', 'Approve and convert admissions'),
    (gen_random_uuid(), 'attendance:read', 'Read attendance records'),
    (gen_random_uuid(), 'attendance:write', 'Record attendance')
ON CONFLICT (name) DO NOTHING;

INSERT INTO roles (id, school_id, name)
VALUES
    (gen_random_uuid(), :'school_id'::uuid, 'admin'),
    (gen_random_uuid(), :'school_id'::uuid, 'staff'),
    (gen_random_uuid(), :'school_id'::uuid, 'super_admin')
ON CONFLICT (school_id, name) DO NOTHING;

INSERT INTO role_permissions (id, role_id, permission_id)
SELECT gen_random_uuid(), r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.school_id = :'school_id'::uuid
  AND r.name = 'admin'
  AND p.name <> 'users:manage'
ON CONFLICT (role_id, permission_id) DO NOTHING;

COMMIT;
