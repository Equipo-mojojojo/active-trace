"""create audit_log table (append-only) + trigger to reject UPDATE/DELETE

Revision ID: 0004_create_audit_log
Revises: 0003_create_rbac_tables
Create Date: 2026-06-02 17:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0004_create_audit_log"
down_revision = "0003_create_rbac_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # audit_log table
    # -----------------------------------------------------------------------
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("impersonado_id", sa.Uuid(), nullable=True),
        sa.Column("materia_id", sa.Uuid(), nullable=True),
        sa.Column("accion", sa.String(100), nullable=False),
        sa.Column("detalle", JSONB(), nullable=True),
        sa.Column("filas_afectadas", sa.Integer(), nullable=True),
        sa.Column("ip", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column(
            "fecha_hora",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(["actor_id"], ["user_account.id"]),
        sa.ForeignKeyConstraint(
            ["impersonado_id"], ["user_account.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_log_tenant_id"), "audit_log", ["tenant_id"])
    op.create_index(op.f("ix_audit_log_actor_id"), "audit_log", ["actor_id"])
    op.create_index(op.f("ix_audit_log_impersonado_id"), "audit_log", ["impersonado_id"])
    op.create_index(op.f("ix_audit_log_materia_id"), "audit_log", ["materia_id"])
    op.create_index(op.f("ix_audit_log_accion"), "audit_log", ["accion"])
    op.create_index(
        op.f("ix_audit_log_fecha_hora"), "audit_log", ["fecha_hora"]
    )

    # -----------------------------------------------------------------------
    # Append-only trigger: reject UPDATE and DELETE on audit_log
    # -----------------------------------------------------------------------
    op.execute(
        """
        CREATE OR REPLACE FUNCTION no_audit_update_delete()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log is append-only: UPDATE and DELETE are not allowed';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_audit_log_append_only
            BEFORE UPDATE OR DELETE ON audit_log
            FOR EACH ROW
            EXECUTE FUNCTION no_audit_update_delete();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_audit_log_append_only ON audit_log")
    op.execute("DROP FUNCTION IF EXISTS no_audit_update_delete()")
    op.drop_index(op.f("ix_audit_log_fecha_hora"), table_name="audit_log")
    op.drop_index(op.f("ix_audit_log_accion"), table_name="audit_log")
    op.drop_index(op.f("ix_audit_log_materia_id"), table_name="audit_log")
    op.drop_index(op.f("ix_audit_log_impersonado_id"), table_name="audit_log")
    op.drop_index(op.f("ix_audit_log_actor_id"), table_name="audit_log")
    op.drop_index(op.f("ix_audit_log_tenant_id"), table_name="audit_log")
    op.drop_table("audit_log")
