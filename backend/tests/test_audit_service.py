"""Tests for AuditService (action registration with validation).

These tests exercise the AuditService against a real PostgreSQL database
via the ``db_session`` fixture, confirming that entries are persisted,
validated, and attributed correctly.
"""

from __future__ import annotations

from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_constants import AuditAction
from app.models.audit_log import AuditLog
from app.services.audit_service import AuditActionError, AuditService
from tests.conftest import create_test_tenant, create_test_user


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
async def _setup_audit_trigger(db_session: AsyncSession) -> None:
    """Ensure the append-only trigger exists for audit_log tests.

    Copied from test_audit_log_model.py — the trigger is normally
    created by Alembic migration 0004.
    """
    from sqlalchemy import text

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
    await db_session.execute(
        text("DROP TRIGGER IF EXISTS trg_audit_log_append_only ON audit_log")
    )
    await db_session.execute(text("DROP FUNCTION IF EXISTS no_audit_update_delete()"))
    await db_session.commit()


@pytest.fixture
async def audit_service(db_session: AsyncSession) -> AuditService:
    """Build an AuditService bound to a test tenant."""
    return AuditService(db=db_session, tenant_id="00000000-0000-0000-0000-000000000000")


# ── Tests ────────────────────────────────────────────────────────────


class TestAuditServiceRegister:
    """AuditService.register() behaviour."""

    @pytest.mark.asyncio
    async def test_register_with_all_fields(
        self, db_session: AsyncSession
    ) -> None:
        """Register an action with every optional field filled."""
        tenant = await create_test_tenant(db_session)
        user = await create_test_user(
            db_session, tenant_id=tenant.id, email="actor@test.com"
        )

        service = AuditService(db=db_session, tenant_id=tenant.id)
        await service.register(
            actor_id=user.id,
            accion=AuditAction.CALIFICACIONES_IMPORTAR,
            detalle={"archivo": "notas.xlsx"},
            filas_afectadas=30,
            ip="203.0.113.42",
            user_agent="pytest-agent",
        )
        await db_session.commit()

        # Verify the entry
        result = await db_session.execute(
            select(AuditLog).where(AuditLog.actor_id == user.id)
        )
        entry = result.scalar_one()
        assert entry.accion == "CALIFICACIONES_IMPORTAR"
        assert entry.detalle == {"archivo": "notas.xlsx"}
        assert entry.filas_afectadas == 30
        assert entry.ip == "203.0.113.42"
        assert entry.user_agent == "pytest-agent"
        assert entry.tenant_id == tenant.id

    @pytest.mark.asyncio
    async def test_register_minimal_fields(
        self, db_session: AsyncSession
    ) -> None:
        """Register an action with only actor_id, tenant_id and accion."""
        tenant = await create_test_tenant(db_session)
        user = await create_test_user(
            db_session, tenant_id=tenant.id, email="minimal@test.com"
        )

        service = AuditService(db=db_session, tenant_id=tenant.id)
        await service.register(
            actor_id=user.id,
            accion=AuditAction.PADRON_CARGAR,
        )
        await db_session.commit()

        result = await db_session.execute(
            select(AuditLog).where(AuditLog.actor_id == user.id)
        )
        entry = result.scalar_one()
        assert entry.accion == "PADRON_CARGAR"
        assert entry.detalle is None
        assert entry.filas_afectadas is None
        assert entry.ip is None
        assert entry.user_agent is None

    @pytest.mark.asyncio
    async def test_register_under_impersonation(
        self, db_session: AsyncSession
    ) -> None:
        """Under impersonation, actor_id is the real user, impersonado_id the target."""
        tenant = await create_test_tenant(db_session)
        admin = await create_test_user(
            db_session, tenant_id=tenant.id, email="admin@test.com"
        )
        soporte = await create_test_user(
            db_session, tenant_id=tenant.id, email="soporte@test.com"
        )

        service = AuditService(db=db_session, tenant_id=tenant.id)
        await service.register(
            actor_id=admin.id,  # real user
            impersonado_id=soporte.id,  # impersonated user
            accion=AuditAction.IMPERSONACION_INICIAR,
        )
        await db_session.commit()

        result = await db_session.execute(
            select(AuditLog).where(AuditLog.accion == "IMPERSONACION_INICIAR")
        )
        entry = result.scalar_one()
        assert entry.actor_id == admin.id
        assert entry.impersonado_id == soporte.id

    @pytest.mark.asyncio
    async def test_invalid_action_raises_error(
        self, db_session: AsyncSession
    ) -> None:
        """An invalid action code raises AuditActionError."""
        tenant = await create_test_tenant(db_session)
        user = await create_test_user(
            db_session, tenant_id=tenant.id, email="actor@invalid.com"
        )

        service = AuditService(db=db_session, tenant_id=tenant.id)
        with pytest.raises(AuditActionError, match="not a valid audit action"):
            await service.register(
                actor_id=user.id,
                accion="CODIGO_INEXISTENTE",  # not in AuditAction enum
            )

    @pytest.mark.asyncio
    async def test_invalid_action_does_not_persist(
        self, db_session: AsyncSession
    ) -> None:
        """When an invalid action is rejected, no entry is persisted."""
        tenant = await create_test_tenant(db_session)
        user = await create_test_user(
            db_session, tenant_id=tenant.id, email="noentry@test.com"
        )

        service = AuditService(db=db_session, tenant_id=tenant.id)
        with pytest.raises(AuditActionError):
            await service.register(
                actor_id=user.id,
                accion="NO_EXISTE",
            )
        await db_session.commit()

        # No audit log entries should exist
        count = await db_session.execute(select(func.count(AuditLog.id)))
        assert count.scalar_one() == 0

    @pytest.mark.asyncio
    async def test_register_with_explicit_ip_override(
        self, db_session: AsyncSession
    ) -> None:
        """Explicit ip/user_agent passed to register() overrides the service-level ones."""
        tenant = await create_test_tenant(db_session)
        user = await create_test_user(
            db_session, tenant_id=tenant.id, email="override@test.com"
        )

        # Service has default IP
        service = AuditService(
            db=db_session,
            tenant_id=tenant.id,
            ip="10.0.0.1",
            user_agent="default-agent",
        )
        # But register() provides explicit overrides
        await service.register(
            actor_id=user.id,
            accion=AuditAction.USUARIO_LOGIN,
            ip="203.0.113.99",
            user_agent="override-agent",
        )
        await db_session.commit()

        result = await db_session.execute(
            select(AuditLog).where(AuditLog.actor_id == user.id)
        )
        entry = result.scalar_one()
        assert entry.ip == "203.0.113.99"
        assert entry.user_agent == "override-agent"

    @pytest.mark.asyncio
    async def test_register_uses_service_level_ip_as_fallback(
        self, db_session: AsyncSession
    ) -> None:
        """When register() omits ip/ua, the service-level defaults are used."""
        tenant = await create_test_tenant(db_session)
        user = await create_test_user(
            db_session, tenant_id=tenant.id, email="fallback@test.com"
        )

        service = AuditService(
            db=db_session,
            tenant_id=tenant.id,
            ip="10.0.0.1",
            user_agent="service-agent",
        )
        await service.register(
            actor_id=user.id,
            accion=AuditAction.USUARIO_LOGOUT,
            # no ip/user_agent — should use service defaults
        )
        await db_session.commit()

        result = await db_session.execute(
            select(AuditLog).where(AuditLog.actor_id == user.id)
        )
        entry = result.scalar_one()
        assert entry.ip == "10.0.0.1"
        assert entry.user_agent == "service-agent"
