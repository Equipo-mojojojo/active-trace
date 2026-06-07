from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.services.comunicacion_dispatcher import ComunicacionDispatcher
from app.services.comunicacion_service import ComunicacionService


async def process_pending_communications(
    session: AsyncSession,
    dispatcher: ComunicacionDispatcher | None = None,
    batch_size: int = 100,
) -> int:
    result = await session.execute(
        select(Tenant.id).where(Tenant.deleted_at.is_(None)).order_by(Tenant.created_at)
    )
    processed = 0
    for tenant_id in result.scalars().all():
        service = ComunicacionService(
            session=session,
            tenant_id=tenant_id,
            dispatcher=dispatcher,
        )
        processed += await service.process_pending_batch(limit=batch_size)
    return processed
