"""Initial school, identity, student, admission and attendance schema."""

import sqlalchemy as sa

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "schools",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.execute("ALTER TABLE schools ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY school_isolation ON schools
        USING (id = NULLIF(current_setting('app.school_id', true), '')::uuid)
        WITH CHECK (id = NULLIF(current_setting('app.school_id', true), '')::uuid)
        """
    )
    op.create_table(
        "permissions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("description", sa.String(255)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "school_id", sa.Uuid(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320)),
        sa.Column("phone", sa.String(32)),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("must_change_password", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_user_profiles_school_id", "user_profiles", ["school_id"])
    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "school_id", sa.Uuid(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("school_id", "name", name="uq_roles_school_name"),
    )
    op.create_index("ix_roles_school_id", "roles", ["school_id"])
    op.create_table(
        "students",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "school_id", sa.Uuid(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("admission_number", sa.String(40), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("date_of_birth", sa.Date()),
        sa.Column("class_name", sa.String(32), nullable=False),
        sa.Column("section", sa.String(32), nullable=False),
        sa.Column("roll_number", sa.String(32), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint(
            "school_id", "admission_number", name="uq_students_school_admission_number"
        ),
        sa.UniqueConstraint(
            "school_id", "class_name", "section", "roll_number", name="uq_students_roll_context"
        ),
        sa.CheckConstraint(
            "status IN ('active', 'inactive', 'graduated', 'transferred')",
            name="ck_students_status",
        ),
    )
    op.create_index("ix_students_school_id", "students", ["school_id"])
    op.create_table(
        "teachers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "school_id", sa.Uuid(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("employee_number", sa.String(40), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(320)),
        sa.Column("phone", sa.String(32)),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint(
            "school_id", "employee_number", name="uq_teachers_school_employee_number"
        ),
        sa.CheckConstraint(
            "status IN ('active', 'inactive', 'on_leave')", name="ck_teachers_status"
        ),
    )
    op.create_index("ix_teachers_school_id", "teachers", ["school_id"])
    op.create_table(
        "admission_applications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "school_id", sa.Uuid(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("application_number", sa.String(40), nullable=False),
        sa.Column("applicant_name", sa.String(200), nullable=False),
        sa.Column("requested_class", sa.String(32), nullable=False),
        sa.Column("guardian_name", sa.String(200), nullable=False),
        sa.Column("guardian_phone", sa.String(32), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("students.id", ondelete="SET NULL")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("school_id", "application_number", name="uq_admissions_school_number"),
        sa.CheckConstraint(
            "status IN ('submitted', 'under_review', 'approved', 'rejected', 'converted')",
            name="ck_admissions_status",
        ),
    )
    op.create_index("ix_admission_applications_school_id", "admission_applications", ["school_id"])
    op.create_table(
        "attendance_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "school_id", sa.Uuid(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "student_id",
            sa.Uuid(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("attendance_date", sa.Date(), nullable=False),
        sa.Column("session", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("remarks", sa.String(500)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint(
            "school_id",
            "student_id",
            "attendance_date",
            "session",
            name="uq_attendance_student_date_session",
        ),
        sa.CheckConstraint(
            "status IN ('present', 'absent', 'late', 'excused')",
            name="ck_attendance_status",
        ),
    )
    op.create_index("ix_attendance_records_school_id", "attendance_records", ["school_id"])
    op.create_index("ix_attendance_records_student_id", "attendance_records", ["student_id"])
    op.create_index(
        "ix_attendance_records_attendance_date", "attendance_records", ["attendance_date"]
    )
    op.create_table(
        "user_roles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("user_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role_id", sa.Uuid(), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])
    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "role_id", sa.Uuid(), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "permission_id",
            sa.Uuid(),
            sa.ForeignKey("permissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_pair"),
    )
    op.create_index("ix_role_permissions_role_id", "role_permissions", ["role_id"])
    op.create_index("ix_role_permissions_permission_id", "role_permissions", ["permission_id"])
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "school_id", sa.Uuid(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("user_profiles.id"), nullable=False),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("resource_type", sa.String(80), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_audit_logs_school_id", "audit_logs", ["school_id"])
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])

    for table in (
        "user_profiles",
        "roles",
        "students",
        "teachers",
        "admission_applications",
        "attendance_records",
        "audit_logs",
    ):
        op.execute(sa.text(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY'))
        op.execute(
            sa.text(
                f"""
                CREATE POLICY school_isolation ON "{table}"
                USING (school_id = NULLIF(current_setting('app.school_id', true), '')::uuid)
                WITH CHECK (school_id = NULLIF(current_setting('app.school_id', true), '')::uuid)
                """
            )
        )
    op.execute("DROP POLICY school_isolation ON user_profiles")
    op.execute(
        """
        CREATE POLICY profile_isolation ON user_profiles
        USING (
            id = NULLIF(current_setting('app.user_id', true), '')::uuid
            OR school_id = NULLIF(current_setting('app.school_id', true), '')::uuid
        )
        WITH CHECK (school_id = NULLIF(current_setting('app.school_id', true), '')::uuid)
        """
    )
    for table in ("user_roles",):
        op.execute(sa.text(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY'))
        op.execute(
            sa.text(
                f"""
                CREATE POLICY user_role_isolation ON "{table}"
                USING (
                    user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
                    OR EXISTS (
                        SELECT 1 FROM user_profiles p
                        WHERE p.id = user_roles.user_id
                        AND p.school_id = NULLIF(current_setting('app.school_id', true), '')::uuid
                    )
                )
                """
            )
        )
    op.execute("ALTER TABLE role_permissions ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY role_permission_isolation ON role_permissions
        USING (EXISTS (
            SELECT 1 FROM roles r
            WHERE r.id = role_permissions.role_id
            AND r.school_id = NULLIF(current_setting('app.school_id', true), '')::uuid
        ))
        """
    )
    op.execute("ALTER TABLE permissions ENABLE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY permissions_read ON permissions FOR SELECT USING (true)")


def downgrade() -> None:
    for table in (
        "audit_logs",
        "role_permissions",
        "user_roles",
        "attendance_records",
        "admission_applications",
        "teachers",
        "students",
        "roles",
        "user_profiles",
        "permissions",
        "schools",
    ):
        op.drop_table(table)
