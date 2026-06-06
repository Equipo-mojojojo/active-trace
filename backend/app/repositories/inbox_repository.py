from __future__ import annotations

from datetime import timezone
from datetime import datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import utc_now
from app.models.mensaje_interno import MensajeInterno
from app.repositories.base import TenantScopedRepository


class InboxRepository(TenantScopedRepository[MensajeInterno]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        super().__init__(session, MensajeInterno, tenant_id)

    async def list_hilos(self, destinatario_id: UUID) -> list[SimpleNamespace]:
        stmt = (
            select(
                MensajeInterno.hilo_id,
                func.min(MensajeInterno.asunto).label("asunto"),
                func.min(MensajeInterno.remitente_id).label("remitente_id"),
                func.count(MensajeInterno.id).label("total_mensajes"),
                func.max(MensajeInterno.created_at).label("ultimo_mensaje_at"),
                func.sum(
                    func.cast(
                        MensajeInterno.leido_at.is_(None)
                        & (MensajeInterno.destinatario_id == destinatario_id),
                        func.Integer if False else type(1),
                    )
                ).label("no_leidos"),
            )
            .where(MensajeInterno.tenant_id == self.tenant_id)
            .where(MensajeInterno.destinatario_id == destinatario_id)
            .where(MensajeInterno.deleted_at.is_(None))
            .group_by(MensajeInterno.hilo_id)
            .order_by(func.max(MensajeInterno.created_at).desc())
        )
        result = await self.session.execute(stmt)
        hilos = []
        for row in result:
            count_no_leidos_stmt = (
                select(func.count(MensajeInterno.id))
                .where(MensajeInterno.tenant_id == self.tenant_id)
                .where(MensajeInterno.hilo_id == row.hilo_id)
                .where(MensajeInterno.destinatario_id == destinatario_id)
                .where(MensajeInterno.leido_at.is_(None))
                .where(MensajeInterno.deleted_at.is_(None))
            )
            no_leidos_result = await self.session.execute(count_no_leidos_stmt)
            no_leidos = no_leidos_result.scalar_one()
            hilos.append(SimpleNamespace(
                hilo_id=row.hilo_id,
                asunto=row.asunto,
                remitente_id=row.remitente_id,
                total_mensajes=row.total_mensajes,
                tiene_no_leidos=no_leidos > 0,
                ultimo_mensaje_at=row.ultimo_mensaje_at,
            ))
        return hilos

    async def get_hilo_mensajes(self, hilo_id: UUID) -> list[MensajeInterno]:
        result = await self.session.execute(
            self._statement()
            .where(MensajeInterno.hilo_id == hilo_id)
            .order_by(MensajeInterno.created_at.asc())
        )
        return list(result.scalars().all())

    async def es_participante(self, hilo_id: UUID, user_id: UUID) -> bool:
        result = await self.session.execute(
            select(MensajeInterno.id)
            .where(MensajeInterno.tenant_id == self.tenant_id)
            .where(MensajeInterno.hilo_id == hilo_id)
            .where(
                (MensajeInterno.remitente_id == user_id)
                | (MensajeInterno.destinatario_id == user_id)
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def marcar_leidos(self, hilo_id: UUID, destinatario_id: UUID) -> None:
        mensajes = await self.get_hilo_mensajes(hilo_id)
        now = utc_now()
        for m in mensajes:
            if m.destinatario_id == destinatario_id and m.leido_at is None:
                m.leido_at = now
        await self.session.flush()

    async def crear_mensaje(
        self,
        hilo_id: UUID,
        remitente_id: UUID,
        destinatario_id: UUID,
        asunto: str,
        cuerpo: str,
    ) -> MensajeInterno:
        return await self.create(
            hilo_id=hilo_id,
            remitente_id=remitente_id,
            destinatario_id=destinatario_id,
            asunto=asunto,
            cuerpo=cuerpo,
        )

    async def iniciar_hilo(
        self,
        remitente_id: UUID,
        destinatario_id: UUID,
        asunto: str,
        cuerpo: str,
    ) -> MensajeInterno:
        hilo_id = uuid4()
        return await self.crear_mensaje(hilo_id, remitente_id, destinatario_id, asunto, cuerpo)
