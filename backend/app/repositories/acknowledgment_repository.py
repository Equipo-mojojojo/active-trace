from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.acknowledgment_aviso import AcknowledgmentAviso
from app.repositories.base import TenantScopedRepository


class AcknowledgmentRepository(TenantScopedRepository[AcknowledgmentAviso]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, AcknowledgmentAviso, tenant_id)

    async def find_by_aviso_usuario(
        self, aviso_id: UUID, usuario_id: UUID
    ) -> AcknowledgmentAviso | None:
        stmt = select(AcknowledgmentAviso).where(
            AcknowledgmentAviso.tenant_id == self.tenant_id,
            AcknowledgmentAviso.aviso_id == aviso_id,
            AcknowledgmentAviso.usuario_id == usuario_id,
            AcknowledgmentAviso.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_by_aviso(self, aviso_id: UUID) -> int:
        stmt = select(func.count()).select_from(AcknowledgmentAviso).where(
            AcknowledgmentAviso.tenant_id == self.tenant_id,
            AcknowledgmentAviso.aviso_id == aviso_id,
            AcknowledgmentAviso.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
