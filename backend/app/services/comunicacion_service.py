from __future__ import annotations

from string import Formatter
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_constants import AuditAction
from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.models.tenant import Tenant
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.comunicacion_repository import ComunicacionRepository
from app.repositories.materia_repository import MateriaRepository
from app.services.audit_service import AuditService
from app.services.comunicacion_dispatcher import (
    ComunicacionDispatchError,
    ComunicacionDispatcher,
)


class ComunicacionForbiddenError(PermissionError):
    pass


class ComunicacionNotFoundError(LookupError):
    pass


class ComunicacionConflictError(RuntimeError):
    pass


def _placeholder_names(template: str) -> set[str]:
    formatter = Formatter()
    return {
        field_name for _, field_name, _, _ in formatter.parse(template) if field_name
    }


def render_template(template: str, context: dict[str, str]) -> str:
    missing = sorted(_placeholder_names(template) - set(context))
    if missing:
        raise ComunicacionConflictError(
            f"Template references unknown variables: {', '.join(missing)}"
        )
    return template.format(**context)


class ComunicacionService:
    def __init__(
        self,
        session: AsyncSession,
        tenant_id: UUID | str,
        audit: AuditService | None = None,
        dispatcher: ComunicacionDispatcher | None = None,
    ):
        self.session = session
        self.tenant_id = UUID(str(tenant_id))
        self.audit = audit
        self.dispatcher = dispatcher or ComunicacionDispatcher()
        self.repo = ComunicacionRepository(session, tenant_id)
        self.asignacion_repo = AsignacionRepository(session, tenant_id)
        self.materia_repo = MateriaRepository(session, tenant_id)

    async def _get_tenant(self) -> Tenant:
        result = await self.session.execute(
            select(Tenant).where(
                Tenant.id == self.tenant_id, Tenant.deleted_at.is_(None)
            )
        )
        tenant = result.scalar_one_or_none()
        if tenant is None:
            raise ComunicacionNotFoundError("Tenant no encontrado")
        return tenant

    async def _assert_actor_scope(self, actor: object, materia_id: UUID) -> None:
        actor_roles = set(getattr(actor, "roles", []))
        if actor_roles & {"ADMIN", "COORDINADOR", "NEXO"}:
            return

        if "PROFESOR" not in actor_roles:
            raise ComunicacionForbiddenError(
                "El actor autenticado no tiene scope para esta materia"
            )

        asignaciones = await self.asignacion_repo.find_vigent_for_user(
            actor.id, self.tenant_id
        )
        if any(asignacion.materia_id == materia_id for asignacion in asignaciones):
            return

        raise ComunicacionForbiddenError(
            "PROFESOR solo puede comunicar sobre materias propias"
        )

    async def _build_preview_items(
        self,
        *,
        materia_id: UUID,
        entrada_padron_ids: list[UUID],
        asunto_template: str,
        cuerpo_template: str,
        actor: object,
    ) -> tuple[bool, list[dict]]:
        await self._assert_actor_scope(actor, materia_id)
        tenant = await self._get_tenant()
        materia = await self.materia_repo.get_by_id(materia_id)
        if materia is None:
            raise ComunicacionNotFoundError("Materia no encontrada")

        requested_ids = list(dict.fromkeys(entrada_padron_ids))
        entries = await self.repo.get_active_entries_for_materia(
            materia_id, requested_ids
        )
        entry_map = {entry.id: entry for entry in entries}
        missing_ids = [
            entry_id for entry_id in requested_ids if entry_id not in entry_map
        ]
        if missing_ids:
            raise ComunicacionNotFoundError(
                "Algunos destinatarios no pertenecen a un padrón activo de la materia"
            )

        preview_items: list[dict] = []
        for entry_id in requested_ids:
            entry = entry_map[entry_id]
            if not entry.email:
                raise ComunicacionConflictError(
                    "No se puede comunicar a un destinatario sin email cargado"
                )
            context = {
                "alumno_nombre": entry.nombre,
                "alumno_apellidos": entry.apellidos,
                "alumno_nombre_completo": f"{entry.nombre} {entry.apellidos}".strip(),
                "materia_nombre": materia.nombre,
                "comision": entry.comision or "",
                "regional": entry.regional or "",
            }
            preview_items.append(
                {
                    "entrada_padron_id": entry.id,
                    "destinatario_nombre": context["alumno_nombre_completo"],
                    "destinatario_email": entry.email,
                    "asunto": render_template(asunto_template, context),
                    "cuerpo": render_template(cuerpo_template, context),
                }
            )

        return bool(
            getattr(tenant, "communication_approval_required", False)
        ), preview_items

    async def preview(
        self,
        *,
        materia_id: UUID,
        entrada_padron_ids: list[UUID],
        asunto_template: str,
        cuerpo_template: str,
        actor: object,
    ) -> dict:
        requiere_aprobacion, preview_items = await self._build_preview_items(
            materia_id=materia_id,
            entrada_padron_ids=entrada_padron_ids,
            asunto_template=asunto_template,
            cuerpo_template=cuerpo_template,
            actor=actor,
        )
        return {
            "requiere_aprobacion": requiere_aprobacion,
            "preview": preview_items,
        }

    async def enqueue(
        self,
        *,
        materia_id: UUID,
        entrada_padron_ids: list[UUID],
        asunto_template: str,
        cuerpo_template: str,
        actor: object,
        audit_actor_id: UUID,
    ) -> dict:
        requiere_aprobacion, preview_items = await self._build_preview_items(
            materia_id=materia_id,
            entrada_padron_ids=entrada_padron_ids,
            asunto_template=asunto_template,
            cuerpo_template=cuerpo_template,
            actor=actor,
        )

        lote_id = uuid4()
        comunicaciones = await self.repo.create_many(
            [
                {
                    "lote_id": lote_id,
                    "entrada_padron_id": item["entrada_padron_id"],
                    "materia_id": materia_id,
                    "destinatario_email": item["destinatario_email"],
                    "destinatario_nombre": item["destinatario_nombre"],
                    "asunto": item["asunto"],
                    "cuerpo": item["cuerpo"],
                    "estado": EstadoComunicacion.PENDIENTE,
                    "requiere_aprobacion": requiere_aprobacion,
                }
                for item in preview_items
            ]
        )

        if self.audit is not None:
            await self.audit.register(
                actor_id=audit_actor_id,
                accion=AuditAction.COMUNICACION_ENVIAR,
                materia_id=materia_id,
                filas_afectadas=len(comunicaciones),
                detalle={
                    "lote_id": str(lote_id),
                    "requiere_aprobacion": requiere_aprobacion,
                },
            )

        return self._serialize_lote(lote_id, comunicaciones)

    async def get_lote(self, lote_id: UUID, actor: object) -> dict:
        comunicaciones = await self.repo.list_by_lote(lote_id)
        if not comunicaciones:
            raise ComunicacionNotFoundError("Lote no encontrado")
        await self._assert_actor_scope(actor, comunicaciones[0].materia_id)
        return self._serialize_lote(lote_id, comunicaciones)

    async def approve_lote(self, lote_id: UUID, actor_id: UUID, actor: object) -> dict:
        comunicaciones = await self.repo.list_by_lote(lote_id)
        if not comunicaciones:
            raise ComunicacionNotFoundError("Lote no encontrado")
        await self._assert_actor_scope(actor, comunicaciones[0].materia_id)

        affected = 0
        for comunicacion in comunicaciones:
            if (
                comunicacion.requiere_aprobacion
                and comunicacion.estado == EstadoComunicacion.PENDIENTE
                and not comunicacion.aprobada
            ):
                comunicacion.aprobar(actor_id)
                affected += 1

        if affected == 0:
            raise ComunicacionConflictError(
                "No hay comunicaciones pendientes de aprobación"
            )

        await self.session.flush()
        if self.audit is not None:
            await self.audit.register(
                actor_id=actor_id,
                accion=AuditAction.COMUNICACION_APROBAR,
                materia_id=comunicaciones[0].materia_id,
                filas_afectadas=affected,
                detalle={"lote_id": str(lote_id)},
            )
        return {"message": "Lote aprobado", "affected": affected}

    async def cancel_lote(self, lote_id: UUID, actor_id: UUID, actor: object) -> dict:
        comunicaciones = await self.repo.list_by_lote(lote_id)
        if not comunicaciones:
            raise ComunicacionNotFoundError("Lote no encontrado")
        await self._assert_actor_scope(actor, comunicaciones[0].materia_id)

        affected = 0
        for comunicacion in comunicaciones:
            if comunicacion.estado == EstadoComunicacion.PENDIENTE:
                comunicacion.cancelar(actor_id)
                affected += 1

        if affected == 0:
            raise ComunicacionConflictError(
                "No hay comunicaciones pendientes para cancelar"
            )

        await self.session.flush()
        if self.audit is not None:
            await self.audit.register(
                actor_id=actor_id,
                accion=AuditAction.COMUNICACION_CANCELAR,
                materia_id=comunicaciones[0].materia_id,
                filas_afectadas=affected,
                detalle={"lote_id": str(lote_id)},
            )
        return {"message": "Lote cancelado", "affected": affected}

    async def approve_one(
        self, comunicacion_id: UUID, actor_id: UUID, actor: object
    ) -> dict:
        comunicacion = await self.repo.get_by_id(comunicacion_id)
        if comunicacion is None:
            raise ComunicacionNotFoundError("Comunicación no encontrada")
        await self._assert_actor_scope(actor, comunicacion.materia_id)
        comunicacion.aprobar(actor_id)
        await self.session.flush()
        if self.audit is not None:
            await self.audit.register(
                actor_id=actor_id,
                accion=AuditAction.COMUNICACION_APROBAR,
                materia_id=comunicacion.materia_id,
                filas_afectadas=1,
                detalle={"comunicacion_id": str(comunicacion.id)},
            )
        return {"message": "Comunicación aprobada", "affected": 1}

    async def cancel_one(
        self, comunicacion_id: UUID, actor_id: UUID, actor: object
    ) -> dict:
        comunicacion = await self.repo.get_by_id(comunicacion_id)
        if comunicacion is None:
            raise ComunicacionNotFoundError("Comunicación no encontrada")
        await self._assert_actor_scope(actor, comunicacion.materia_id)
        comunicacion.cancelar(actor_id)
        await self.session.flush()
        if self.audit is not None:
            await self.audit.register(
                actor_id=actor_id,
                accion=AuditAction.COMUNICACION_CANCELAR,
                materia_id=comunicacion.materia_id,
                filas_afectadas=1,
                detalle={"comunicacion_id": str(comunicacion.id)},
            )
        return {"message": "Comunicación cancelada", "affected": 1}

    async def process_pending_batch(self, limit: int = 100) -> int:
        comunicaciones = await self.repo.get_pending_eligible(limit=limit)
        processed = 0

        for comunicacion in comunicaciones:
            comunicacion.marcar_enviando()
            await self.session.flush()
            try:
                await self.dispatcher.send(comunicacion)
            except ComunicacionDispatchError as exc:
                comunicacion.marcar_error(str(exc))
            except Exception as exc:
                comunicacion.marcar_error(str(exc))
            else:
                comunicacion.marcar_enviada()
            processed += 1

        await self.session.flush()
        return processed

    def _serialize_lote(
        self, lote_id: UUID, comunicaciones: list[Comunicacion]
    ) -> dict:
        requiere_aprobacion = any(c.requiere_aprobacion for c in comunicaciones)
        return {
            "lote_id": lote_id,
            "total": len(comunicaciones),
            "requiere_aprobacion": requiere_aprobacion,
            "comunicaciones": [
                {
                    "id": comunicacion.id,
                    "lote_id": comunicacion.lote_id,
                    "entrada_padron_id": comunicacion.entrada_padron_id,
                    "destinatario_nombre": comunicacion.destinatario_nombre,
                    "estado": comunicacion.estado,
                    "requiere_aprobacion": comunicacion.requiere_aprobacion,
                    "aprobada": comunicacion.aprobada,
                    "error_detalle": comunicacion.error_detalle,
                }
                for comunicacion in comunicaciones
            ],
        }
