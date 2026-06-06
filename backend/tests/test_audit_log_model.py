from __future__ import annotations

from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from tests.conftest import create_test_tenant, create_test_user


@pytest.fixture(autouse=True)
async def _setup_audit_trigger(db_session: AsyncSession) -> None:
    """Create the append-only trigger for audit_log in the test DB.

    The trigger is normally created by Alembic migration 0004, but
    the ``db_session`` fixture uses ``create_all`` from metadata, so
    we apply the trigger manually for test isolation.
    """
    await db_session.execute(
        text(
            """
            CREATE OR REPLACE FUNCTION no_audit_update_delete()
            RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'audit_log is append-only: UPDATE and DELETE are not allowed';
            END;
            $$ LANGUAGE plpgsql;
            """
        )
    )
    await db_session.execute(
        text(
            """
            CREATE TRIGGER trg_audit_log_append_only
                BEFORE UPDATE OR DELETE ON audit_log
                FOR EACH ROW
                EXECUTE FUNCTION no_audit_update_delete();
            """
        )
    )
    await db_session.commit()
    yield
    await db_session.execute(text("DROP TRIGGER IF EXISTS trg_audit_log_append_only ON audit_log"))
    await db_session.execute(text("DROP FUNCTION IF EXISTS no_audit_update_delete()"))
    await db_session.commit()


# ===================================================================
# 1.5 — Model creation tests
# ===================================================================


@pytest.mark.asyncio
async def test_create_audit_log_entry(db_session: AsyncSession) -> None:
    """Create a basic audit log entry with required fields."""
    tenant = await create_test_tenant(db_session)
    user = await create_test_user(db_session, tenant_id=tenant.id, email="actor@test.com")

    entry = AuditLog(
        tenant_id=tenant.id,
        actor_id=user.id,
        accion="CALIFICACIONES_IMPORTAR",
        detalle={"archivo": "calificaciones.xlsx"},
        filas_afectadas=42,
        ip="203.0.113.42",
        user_agent="Mozilla/5.0",
    )
    db_session.add(entry)
    await db_session.commit()
    await db_session.refresh(entry)

    assert entry.id is not None
    assert isinstance(entry.id, UUID)
    assert entry.accion == "CALIFICACIONES_IMPORTAR"
    assert entry.detalle == {"archivo": "calificaciones.xlsx"}
    assert entry.filas_afectadas == 42
    assert entry.ip == "203.0.113.42"
    assert entry.user_agent == "Mozilla/5.0"
    assert entry.impersonado_id is None
    assert entry.materia_id is None
    assert entry.fecha_hora is not None


@pytest.mark.asyncio
async def test_create_audit_log_minimal_fields(db_session: AsyncSession) -> None:
    """Create an audit log entry with only required fields."""
    tenant = await create_test_tenant(db_session)
    user = await create_test_user(db_session, tenant_id=tenant.id, email="minimal@test.com")

    entry = AuditLog(
        tenant_id=tenant.id,
        actor_id=user.id,
        accion="PADRON_CARGAR",
    )
    db_session.add(entry)
    await db_session.commit()
    await db_session.refresh(entry)

    assert entry.accion == "PADRON_CARGAR"
    assert entry.detalle is None
    assert entry.filas_afectadas is None
    assert entry.ip is None
    assert entry.user_agent is None


@pytest.mark.asyncio
async def test_audit_log_impersonation_fields(db_session: AsyncSession) -> None:
    """Create audit log entry with impersonado_id."""
    tenant = await create_test_tenant(db_session)
    actor = await create_test_user(db_session, tenant_id=tenant.id, email="admin@test.com")
    impersonated = await create_test_user(
        db_session, tenant_id=tenant.id, email="user@test.com"
    )

    entry = AuditLog(
        tenant_id=tenant.id,
        actor_id=actor.id,
        impersonado_id=impersonated.id,
        accion="IMPERSONACION_INICIAR",
    )
    db_session.add(entry)
    await db_session.commit()
    await db_session.refresh(entry)

    assert entry.actor_id == actor.id
    assert entry.impersonado_id == impersonated.id


# ===================================================================
# 2.1 & 2.2 — Append-only enforcement tests
# ===================================================================


@pytest.mark.asyncio
async def test_audit_log_rejects_update(db_session: AsyncSession) -> None:
    """UPDATE on audit_log is rejected by the trigger."""
    tenant = await create_test_tenant(db_session)
    user = await create_test_user(db_session, tenant_id=tenant.id, email="u@test.com")

    entry = AuditLog(tenant_id=tenant.id, actor_id=user.id, accion="TEST")
    db_session.add(entry)
    await db_session.commit()

    with pytest.raises(Exception, match="append-only"):
        await db_session.execute(
            text("UPDATE audit_log SET accion = 'HACKED' WHERE id = :id"),
            {"id": entry.id},
        )
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_audit_log_rejects_delete(db_session: AsyncSession) -> None:
    """DELETE on audit_log is rejected by the trigger."""
    tenant = await create_test_tenant(db_session)
    user = await create_test_user(db_session, tenant_id=tenant.id, email="u2@test.com")

    entry = AuditLog(tenant_id=tenant.id, actor_id=user.id, accion="TEST")
    db_session.add(entry)
    await db_session.commit()

    with pytest.raises(Exception, match="append-only"):
        await db_session.execute(
            text("DELETE FROM audit_log WHERE id = :id"),
            {"id": entry.id},
        )
        await db_session.commit()
    await db_session.rollback()
