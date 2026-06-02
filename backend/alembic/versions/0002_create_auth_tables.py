"""create auth tables

Revision ID: 0002_create_auth_tables
Revises: 0001_create_tenant
Create Date: 2026-06-02 15:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_create_auth_tables"
down_revision = "0001_create_tenant"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_account",
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("email_lookup", sa.String(length=64), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("roles", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("two_factor_enabled", sa.Boolean(), nullable=False),
        sa.Column("totp_secret", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email_lookup", name="uq_user_account_email_lookup"),
    )
    op.create_index(
        op.f("ix_user_account_deleted_at"), "user_account", ["deleted_at"], unique=False
    )
    op.create_index(
        op.f("ix_user_account_email_lookup"),
        "user_account",
        ["email_lookup"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_account_tenant_id"), "user_account", ["tenant_id"], unique=False
    )

    op.create_table(
        "auth_session",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_rotated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user_account.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_auth_session_deleted_at"), "auth_session", ["deleted_at"], unique=False
    )
    op.create_index(
        op.f("ix_auth_session_tenant_id"), "auth_session", ["tenant_id"], unique=False
    )
    op.create_index(
        op.f("ix_auth_session_user_id"), "auth_session", ["user_id"], unique=False
    )

    op.create_table(
        "auth_refresh_token",
        sa.Column("auth_session_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["auth_session_id"], ["auth_session.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user_account.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        op.f("ix_auth_refresh_token_auth_session_id"),
        "auth_refresh_token",
        ["auth_session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auth_refresh_token_deleted_at"),
        "auth_refresh_token",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auth_refresh_token_tenant_id"),
        "auth_refresh_token",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auth_refresh_token_token_hash"),
        "auth_refresh_token",
        ["token_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auth_refresh_token_user_id"),
        "auth_refresh_token",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "password_reset_token",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("token_value", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user_account.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        op.f("ix_password_reset_token_deleted_at"),
        "password_reset_token",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_password_reset_token_tenant_id"),
        "password_reset_token",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_password_reset_token_token_hash"),
        "password_reset_token",
        ["token_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_password_reset_token_user_id"),
        "password_reset_token",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "auth_login_attempt",
        sa.Column("email_lookup", sa.String(length=64), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=False),
        sa.Column("was_successful", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_auth_login_attempt_deleted_at"),
        "auth_login_attempt",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auth_login_attempt_email_lookup"),
        "auth_login_attempt",
        ["email_lookup"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auth_login_attempt_ip_address"),
        "auth_login_attempt",
        ["ip_address"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_auth_login_attempt_ip_address"), table_name="auth_login_attempt"
    )
    op.drop_index(
        op.f("ix_auth_login_attempt_email_lookup"), table_name="auth_login_attempt"
    )
    op.drop_index(
        op.f("ix_auth_login_attempt_deleted_at"), table_name="auth_login_attempt"
    )
    op.drop_table("auth_login_attempt")

    op.drop_index(
        op.f("ix_password_reset_token_user_id"), table_name="password_reset_token"
    )
    op.drop_index(
        op.f("ix_password_reset_token_token_hash"), table_name="password_reset_token"
    )
    op.drop_index(
        op.f("ix_password_reset_token_tenant_id"), table_name="password_reset_token"
    )
    op.drop_index(
        op.f("ix_password_reset_token_deleted_at"), table_name="password_reset_token"
    )
    op.drop_table("password_reset_token")

    op.drop_index(
        op.f("ix_auth_refresh_token_user_id"), table_name="auth_refresh_token"
    )
    op.drop_index(
        op.f("ix_auth_refresh_token_token_hash"), table_name="auth_refresh_token"
    )
    op.drop_index(
        op.f("ix_auth_refresh_token_tenant_id"), table_name="auth_refresh_token"
    )
    op.drop_index(
        op.f("ix_auth_refresh_token_deleted_at"), table_name="auth_refresh_token"
    )
    op.drop_index(
        op.f("ix_auth_refresh_token_auth_session_id"), table_name="auth_refresh_token"
    )
    op.drop_table("auth_refresh_token")

    op.drop_index(op.f("ix_auth_session_user_id"), table_name="auth_session")
    op.drop_index(op.f("ix_auth_session_tenant_id"), table_name="auth_session")
    op.drop_index(op.f("ix_auth_session_deleted_at"), table_name="auth_session")
    op.drop_table("auth_session")

    op.drop_index(op.f("ix_user_account_tenant_id"), table_name="user_account")
    op.drop_index(op.f("ix_user_account_email_lookup"), table_name="user_account")
    op.drop_index(op.f("ix_user_account_deleted_at"), table_name="user_account")
    op.drop_table("user_account")
