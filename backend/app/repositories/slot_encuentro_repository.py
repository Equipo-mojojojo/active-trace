from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.slot_encuentro import SlotEncuentro
from app.repositories.base import TenantScopedRepository


class SlotEncuentroRepository(TenantScopedRepository[SlotEncuentro]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, SlotEncuentro, tenant_id)
