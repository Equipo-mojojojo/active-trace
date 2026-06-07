from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mensaje_interno import MensajeInterno
from app.repositories.inbox_repository import InboxRepository
from app.repositories.usuario_repository import UsuarioRepository


class InboxForbiddenError(PermissionError):
    pass


class InboxNotFoundError(LookupError):
    pass


class InboxConflictError(RuntimeError):
    pass


def validar_destinatario(remitente_id: UUID, destinatario_id: UUID) -> None:
    """Pure function: raise ValueError if remitente == destinatario."""
    if remitente_id == destinatario_id:
        raise ValueError("no puede enviarse un mensaje a sí mismo (mismo user)")


class InboxService:
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        self.session = session
        self.tenant_id = UUID(str(tenant_id))
        self._repo = InboxRepository(session, tenant_id)
        self._usuario_repo = UsuarioRepository(session, tenant_id)

    async def listar_hilos(self, user_id: UUID) -> list[SimpleNamespace]:
        return await self._repo.list_hilos(user_id)

    async def leer_hilo(self, hilo_id: UUID, user_id: UUID) -> list[MensajeInterno]:
        if not await self._repo.es_participante(hilo_id, user_id):
            raise InboxForbiddenError("no_participante")
        mensajes = await self._repo.get_hilo_mensajes(hilo_id)
        if not mensajes:
            raise InboxNotFoundError("hilo_not_found")
        await self._repo.marcar_leidos(hilo_id, user_id)
        return mensajes

    async def responder(self, hilo_id: UUID, user_id: UUID, cuerpo: str) -> MensajeInterno:
        if not await self._repo.es_participante(hilo_id, user_id):
            raise InboxForbiddenError("no_participante")
        mensajes = await self._repo.get_hilo_mensajes(hilo_id)
        if not mensajes:
            raise InboxNotFoundError("hilo_not_found")
        primer = mensajes[0]
        destinatario_id = (
            primer.remitente_id if primer.destinatario_id == user_id else primer.destinatario_id
        )
        return await self._repo.crear_mensaje(
            hilo_id=hilo_id,
            remitente_id=user_id,
            destinatario_id=destinatario_id,
            asunto=primer.asunto,
            cuerpo=cuerpo,
        )

    async def iniciar_hilo(
        self, remitente_id: UUID, destinatario_id: UUID, asunto: str, cuerpo: str
    ) -> MensajeInterno:
        try:
            validar_destinatario(remitente_id, destinatario_id)
        except ValueError as exc:
            raise InboxConflictError(str(exc)) from exc
        destinatario = await self._usuario_repo.get_by_id(destinatario_id)
        if destinatario is None:
            raise InboxNotFoundError("destinatario_not_found")
        return await self._repo.iniciar_hilo(remitente_id, destinatario_id, asunto, cuerpo)
