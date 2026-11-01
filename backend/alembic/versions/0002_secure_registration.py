"""Secure OTP registration, account approval, and Super Admin controls."""

import sqlalchemy as sa

from alembic import op

revision = "0002_secure_registration"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_profiles", sa.Column("employee_id", sa.String(64), nullable=True))
    op.add_column("user_profiles", sa.Column("department", sa.String(120), nullable=True))
    op.add_column("user_profiles", sa.Column("designation", sa.String(120), nullable=True))
    op.add_column("user_profiles", sa.Column("staff_category", sa.String(64), nullable=True))
    op.add_column(
        "user_profiles",
        sa.Column("account_status", sa.String(40), nullable=False, server_default="pending"),
    )
    op.add_column(
        "user_profiles",
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "user_profiles", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.execute(
        """
        UPDATE user_profiles
        SET account_status = CASE WHEN is_active THEN 'approved' ELSE 'disabled' END,
            email_verified = (email IS NOT NULL)
        """
    )
    op.create_check_constraint(
        "ck_user_profiles_account_status",
        "user_profiles",
        "account_status IN ('pending_email_verification', 'pending', 'approved', "
        "'rejected', 'suspended', 'disabled')",
    )
    op.create_index(
        "uq_user_profiles_email_lower",
        "user_profiles",
        [sa.text("lower(email)")],
        unique=True,
        postgresql_where=sa.text("email IS NOT NULL"),
    )

    op.add_column(
        "user_roles",
        sa.Column("assigned_by", sa.Uuid(), sa.ForeignKey("user_profiles.id", ondelete="SET NULL")),
    )
    op.add_column(
        "user_roles",
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.add_column(
        "user_roles",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "registration_requests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "school_id", sa.Uuid(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "applicant_user_id",
            sa.Uuid(),
            sa.ForeignKey("user_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("phone_number", sa.String(32), nullable=False),
        sa.Column("employee_id", sa.String(64)),
        sa.Column("department", sa.String(120), nullable=False),
        sa.Column("designation", sa.String(120), nullable=False),
        sa.Column("staff_category", sa.String(64)),
        sa.Column("requested_role", sa.String(16), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("rejection_reason", sa.Text()),
        sa.Column("reviewed_by", sa.Uuid(), sa.ForeignKey("user_profiles.id", ondelete="SET NULL")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "requested_role IN ('admin', 'staff')", name="ck_registration_requests_role"
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_registration_requests_status",
        ),
    )
    op.create_index(
        "ix_registration_requests_applicant_user_id", "registration_requests", ["applicant_user_id"]
    )
    op.create_index("ix_registration_requests_email", "registration_requests", ["email"])
    op.create_index(
        "ix_registration_requests_school_status",
        "registration_requests",
        ["school_id", "status"],
    )
    op.create_index(
        "uq_registration_requests_pending_email",
        "registration_requests",
        ["email"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )

    op.create_table(
        "user_permissions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("user_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "permission_id",
            sa.Uuid(),
            sa.ForeignKey("permissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("assigned_by", sa.Uuid(), sa.ForeignKey("user_profiles.id"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("user_id", "permission_id", name="uq_user_permissions_pair"),
    )
    op.create_index("ix_user_permissions_user_id", "user_permissions", ["user_id"])

    op.create_table(
        "system_settings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("key", sa.String(100), nullable=False, unique=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_table(
        "account_audit_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "school_id", sa.Uuid(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "actor_user_id", sa.Uuid(), sa.ForeignKey("user_profiles.id", ondelete="SET NULL")
        ),
        sa.Column(
            "target_user_id", sa.Uuid(), sa.ForeignKey("user_profiles.id", ondelete="SET NULL")
        ),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("previous_status", sa.String(40)),
        sa.Column("new_status", sa.String(40)),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_account_audit_logs_school_id", "account_audit_logs", ["school_id"])
    op.create_index("ix_account_audit_logs_actor_user_id", "account_audit_logs", ["actor_user_id"])
    op.create_index(
        "ix_account_audit_logs_target_user_id", "account_audit_logs", ["target_user_id"]
    )
    op.create_index("ix_account_audit_logs_created_at", "account_audit_logs", ["created_at"])

    for table in ("registration_requests", "account_audit_logs"):
        op.execute(sa.text(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY'))
    op.execute("ALTER TABLE user_permissions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE system_settings ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY registration_request_read ON registration_requests
        FOR SELECT USING (
            applicant_user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
            OR (
                school_id = NULLIF(current_setting('app.school_id', true), '')::uuid
                AND current_setting('app.is_super_admin', true) = 'true'
            )
        )
        """
    )
    op.execute(
        """
        CREATE POLICY registration_request_submit ON registration_requests
        FOR INSERT WITH CHECK (
            applicant_user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
            AND school_id = NULLIF(current_setting('app.school_id', true), '')::uuid
            AND status = 'pending'
            AND email_verified = true
            AND EXISTS (
                SELECT 1 FROM user_profiles p
                WHERE p.id = registration_requests.applicant_user_id
                AND p.school_id = registration_requests.school_id
                AND p.account_status = 'pending'
                AND p.email_verified = true
                AND lower(p.email) = lower(registration_requests.email)
            )
        )
        """
    )
    op.execute(
        """
        CREATE POLICY registration_request_super_admin_update ON registration_requests
        FOR UPDATE
        USING (
            school_id = NULLIF(current_setting('app.school_id', true), '')::uuid
            AND current_setting('app.is_super_admin', true) = 'true'
        )
        WITH CHECK (
            school_id = NULLIF(current_setting('app.school_id', true), '')::uuid
            AND current_setting('app.is_super_admin', true) = 'true'
        )
        """
    )
    op.execute(
        """
        CREATE POLICY account_audit_access ON account_audit_logs
        USING (
            school_id = NULLIF(current_setting('app.school_id', true), '')::uuid
            AND current_setting('app.is_super_admin', true) = 'true'
        )
        WITH CHECK (
            school_id = NULLIF(current_setting('app.school_id', true), '')::uuid
            AND current_setting('app.is_super_admin', true) = 'true'
        )
        """
    )
    op.execute(
        """
        CREATE POLICY user_permissions_access ON user_permissions
        USING (
            user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
            OR current_setting('app.is_super_admin', true) = 'true'
        )
        WITH CHECK (current_setting('app.is_super_admin', true) = 'true')
        """
    )
    op.execute("DROP POLICY user_role_isolation ON user_roles")
    op.execute(
        """
        CREATE POLICY user_role_read ON user_roles
        FOR SELECT
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
    op.execute(
        """
        CREATE POLICY user_role_super_admin_write ON user_roles
        FOR ALL
        USING (current_setting('app.is_super_admin', true) = 'true')
        WITH CHECK (current_setting('app.is_super_admin', true) = 'true')
        """
    )
    op.execute("DROP POLICY role_permission_isolation ON role_permissions")
    op.execute(
        """
        CREATE POLICY role_permission_read ON role_permissions
        FOR SELECT
        USING (EXISTS (
            SELECT 1 FROM roles r
            WHERE r.id = role_permissions.role_id
            AND r.school_id = NULLIF(current_setting('app.school_id', true), '')::uuid
        ))
        """
    )
    op.execute(
        """
        CREATE POLICY role_permission_super_admin_write ON role_permissions
        FOR ALL
        USING (current_setting('app.is_super_admin', true) = 'true')
        WITH CHECK (current_setting('app.is_super_admin', true) = 'true')
        """
    )
    op.execute(
        """
        CREATE POLICY system_settings_super_admin ON system_settings
        USING (current_setting('app.is_super_admin', true) = 'true')
        WITH CHECK (current_setting('app.is_super_admin', true) = 'true')
        """
    )
    op.execute(
        """
        INSERT INTO system_settings (id, key, value)
        VALUES (gen_random_uuid(), 'super_admin_bootstrap_completed', 'false')
        ON CONFLICT (key) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY registration_request_super_admin_update ON registration_requests")
    op.execute("DROP POLICY registration_request_submit ON registration_requests")
    op.execute("DROP POLICY registration_request_read ON registration_requests")
    op.execute(
        """
        CREATE POLICY registration_request_access ON registration_requests
        USING (
            applicant_user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
            OR (
                school_id = NULLIF(current_setting('app.school_id', true), '')::uuid
                AND current_setting('app.is_super_admin', true) = 'true'
            )
        )
        WITH CHECK (
            applicant_user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
            AND school_id = NULLIF(current_setting('app.school_id', true), '')::uuid
        )
        """
    )
    op.execute("DROP POLICY role_permission_super_admin_write ON role_permissions")
    op.execute("DROP POLICY role_permission_read ON role_permissions")
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
    op.execute("DROP POLICY user_role_super_admin_write ON user_roles")
    op.execute("DROP POLICY user_role_read ON user_roles")
    op.execute(
        """
        CREATE POLICY user_role_isolation ON user_roles
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
    for table in (
        "account_audit_logs",
        "system_settings",
        "user_permissions",
        "registration_requests",
    ):
        op.drop_table(table)
    op.drop_index("uq_user_profiles_email_lower", table_name="user_profiles")
    op.drop_constraint("ck_user_profiles_account_status", "user_profiles", type_="check")
    op.drop_column("user_roles", "is_active")
    op.drop_column("user_roles", "assigned_at")
    op.drop_column("user_roles", "assigned_by")
    for column in (
        "last_login_at",
        "email_verified",
        "account_status",
        "staff_category",
        "designation",
        "department",
        "employee_id",
    ):
        op.drop_column("user_profiles", column)
