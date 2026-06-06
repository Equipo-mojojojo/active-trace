"""create tenant table

Revision ID: 0001_create_tenant
Revises:
Create Date: 2026-06-02 14:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_create_tenant"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenant",
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
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
        sa.UniqueConstraint("slug"),
    )
    op.create_index(
        op.f("ix_tenant_deleted_at"), "tenant", ["deleted_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_tenant_deleted_at"), table_name="tenant")
    op.drop_table("tenant")
