"""
EquiposService: Business logic for equipo-docente operations (C-08).

Coordinates EquiposRepository + AuditService. Enforces:
- Multi-tenancy (tenant scoped via repository)
- Audit (ASIGNACION_MODIFICAR per operation)
- Atomicity on asignacion_masiva (conflict → 409)
- RN-12: clonado de vigentes con nuevas fechas
- RN-30: asignación masiva en transacción única

Architecture rule: Queries ONLY in repositories. Logic ONLY here.
"""

from __future__ import annotations

import csv
import io
from datetime import date
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_constants import AuditAction
from app.repositories.equipos_repository import EquiposRepository
from app.schemas.equipos import (
    AsignacionMasivaRequest,
    AsignacionMasivaResponse,
    AsignacionResponse,
    ClonarEquipoRequest,
    ClonarEquipoResponse,
    MisEquiposFiltros,
    ModificarVigenciaRequest,
    ModificarVigenciaResponse,
)
from app.services.audit_service import AuditService


class EquiposConflictError(Exception):
    """Raised when a bulk assignment conflicts with existing data (RN-30)."""

    def __init__(self, message: str, conflictos: list[str] | None = None):
        super().__init__(message)
        self.conflictos = conflictos or []


class EquiposNotFoundError(Exception):
    """Raised when a team has no assignments to operate on."""


class EquiposService:
    """Domain service for equipo-docente management."""

    def __init__(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        audit: AuditService | None = None,
    ):
        self.session = session
        self.tenant_id = tenant_id
        self.repository = EquiposRepository(session, tenant_id)
        self._audit = audit

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _registrar_auditoria(
        self,
        actor_id: UUID,
        detalle: dict | None = None,
        filas_afectadas: int | None = None,
    ) -> None:
        """Register ASIGNACION_MODIFICAR audit entry. No-op if no AuditService."""
        if self._audit is None:
            return
        await self._audit.register(
            actor_id=actor_id,
            accion=AuditAction.ASIGNACION_MODIFICAR,
            detalle=detalle,
            filas_afectadas=filas_afectadas,
        )

    # ------------------------------------------------------------------
    # 1.3 Domain methods — read
    # ------------------------------------------------------------------

    async def mis_equipos(
        self,
        actor_id: UUID,
        filtros: MisEquiposFiltros,
    ) -> list[AsignacionResponse]:
        """
        Return all assignments for the authenticated actor.

        Spec: equipos-mis-equipos — no extra permission required.
        Scope is automatically limited to the actor's own assignments + tenant.

        Args:
            actor_id: ID of the authenticated user.
            filtros: Optional filters.

        Returns:
            List of AsignacionResponse DTOs.
        """
        filtros_dict = filtros.model_dump(exclude_none=True)
        asignaciones = await self.repository.listar_por_usuario(
            usuario_id=actor_id,
            filtros=filtros_dict,
        )
        return [AsignacionResponse.from_orm(a) for a in asignaciones]

    async def consultar_asignaciones(
        self,
        filtros: MisEquiposFiltros,
    ) -> list[AsignacionResponse]:
        """
        Return all assignments in the tenant (COORDINADOR view).

        Spec: equipos-gestion-coordinador — requires equipos:asignar.
        Permission check is enforced at the router layer.

        Args:
            filtros: Optional filters.

        Returns:
            List of AsignacionResponse DTOs.
        """
        filtros_dict = filtros.model_dump(exclude_none=True)
        asignaciones = await self.repository.listar_por_tenant(filtros=filtros_dict)
        return [AsignacionResponse.from_orm(a) for a in asignaciones]

    # ------------------------------------------------------------------
    # 1.5 Asignacion masiva (RN-30 — transacción única)
    # ------------------------------------------------------------------

    async def asignacion_masiva(
        self,
        actor_id: UUID,
        payload: AsignacionMasivaRequest,
    ) -> AsignacionMasivaResponse:
        """
        Create N assignments in a single atomic transaction (RN-30).

        If ANY assignment conflicts (same usuario × rol × materia × carrera × cohorte,
        with overlapping vigency), the entire operation is rejected and
        EquiposConflictError is raised with the list of conflicting usuario_ids.

        Conflict detection is done at service level (no DB unique constraint on
        Asignacion). The operation validates before inserting so the DB transaction
        stays clean.

        Args:
            actor_id: Coordinator/admin performing the action.
            payload: AsignacionMasivaRequest.

        Returns:
            AsignacionMasivaResponse with created count and DTOs.

        Raises:
            EquiposConflictError: If a duplicate assignment is detected.
        """
        from sqlalchemy import and_, select
        from app.models.asignacion import Asignacion

        # Pre-check: validate no existing vigent assignment for each usuario
        today = payload.desde  # Check overlap relative to the new assignment start
        conflictos = []
        for uid in payload.usuarios:
            stmt = (
                select(Asignacion)
                .where(
                    and_(
                        Asignacion.tenant_id == self.tenant_id,
                        Asignacion.usuario_id == uid,
                        Asignacion.rol == payload.rol,
                        Asignacion.materia_id == payload.materia_id,
                        Asignacion.carrera_id == payload.carrera_id,
                        Asignacion.cohorte_id == payload.cohorte_id,
                        Asignacion.deleted_at.is_(None),
                        # Overlap: existing hasta is None or >= new desde
                        (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= payload.desde),
                    )
                )
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing is not None:
                conflictos.append(str(uid))

        if conflictos:
            raise EquiposConflictError(
                f"Conflicto: los siguientes usuarios ya tienen una asignación activa: "
                f"{', '.join(conflictos)}",
                conflictos=conflictos,
            )

        datos = [
            {
                "tenant_id": self.tenant_id,
                "usuario_id": uid,
                "rol": payload.rol,
                "materia_id": payload.materia_id,
                "carrera_id": payload.carrera_id,
                "cohorte_id": payload.cohorte_id,
                "comisiones": payload.comisiones,
                "responsable_id": payload.responsable_id,
                "desde": payload.desde,
                "hasta": payload.hasta,
            }
            for uid in payload.usuarios
        ]

        try:
            creadas = await self.repository.crear_masivo(datos)
        except IntegrityError as exc:
            await self.session.rollback()
            raise EquiposConflictError(
                "Conflicto en asignación masiva: una o más asignaciones ya existen.",
                conflictos=[str(exc)],
            ) from exc

        # Audit: one entry per created assignment (spec section 6)
        for asig in creadas:
            await self._registrar_auditoria(
                actor_id=actor_id,
                detalle={"asignacion_id": str(asig.id), "usuario_id": str(asig.usuario_id)},
            )

        await self.session.commit()
        return AsignacionMasivaResponse(
            creadas=len(creadas),
            asignaciones=[AsignacionResponse.from_orm(a) for a in creadas],
        )

    # ------------------------------------------------------------------
    # 1.4 Clonar equipo (RN-12)
    # ------------------------------------------------------------------

    async def clonar_equipo(
        self,
        actor_id: UUID,
        payload: ClonarEquipoRequest,
    ) -> ClonarEquipoResponse:
        """
        Duplicate vigent assignments of an origin team to a destination cohorte.

        Design D3: only vigent assignments are cloned; origin is not modified.
        Assignments with hasta=NULL receive payload.hasta (new period's end).
        Returns clonadas=0 with a warning message if no vigent assignments exist.

        Args:
            actor_id: Coordinator/admin performing the action.
            payload: ClonarEquipoRequest.

        Returns:
            ClonarEquipoResponse.
        """
        clonadas = await self.repository.clonar_equipo(
            materia_id=payload.materia_id,
            carrera_id=payload.carrera_id,
            cohorte_id_origen=payload.cohorte_id_origen,
            cohorte_id_destino=payload.cohorte_id_destino,
            nueva_desde=payload.desde,
            nueva_hasta=payload.hasta,
        )

        if not clonadas:
            return ClonarEquipoResponse(
                clonadas=0,
                mensaje="El equipo origen no tiene asignaciones vigentes para clonar.",
                asignaciones=[],
            )

        # Audit: one entry per cloned assignment
        for asig in clonadas:
            await self._registrar_auditoria(
                actor_id=actor_id,
                detalle={
                    "asignacion_id": str(asig.id),
                    "usuario_id": str(asig.usuario_id),
                    "cohorte_destino": str(asig.cohorte_id),
                },
            )

        await self.session.commit()
        return ClonarEquipoResponse(
            clonadas=len(clonadas),
            mensaje=f"Clonadas {len(clonadas)} asignaciones.",
            asignaciones=[AsignacionResponse.from_orm(a) for a in clonadas],
        )

    # ------------------------------------------------------------------
    # Modificar vigencia en bloque
    # ------------------------------------------------------------------

    async def modificar_vigencia(
        self,
        actor_id: UUID,
        payload: ModificarVigenciaRequest,
    ) -> ModificarVigenciaResponse:
        """
        Bulk update desde/hasta for a team's assignments.

        dry_run=True returns the count without modifying the DB.
        Raises EquiposNotFoundError if the team has no assignments.
        Audit: one entry per affected assignment (only when not dry_run).

        Args:
            actor_id: Coordinator/admin performing the action.
            payload: ModificarVigenciaRequest.

        Returns:
            ModificarVigenciaResponse.

        Raises:
            EquiposNotFoundError: If team has no assignments.
        """
        afectadas = await self.repository.actualizar_vigencia_equipo(
            materia_id=payload.materia_id,
            carrera_id=payload.carrera_id,
            cohorte_id=payload.cohorte_id,
            nueva_desde=payload.desde,
            nueva_hasta=payload.hasta,
            dry_run=payload.dry_run,
        )

        if afectadas == 0 and not payload.dry_run:
            raise EquiposNotFoundError(
                "No se encontraron asignaciones para el equipo indicado."
            )

        # Audit: only when executing (not dry_run)
        if not payload.dry_run and afectadas > 0:
            for _ in range(afectadas):
                await self._registrar_auditoria(
                    actor_id=actor_id,
                    detalle={
                        "materia_id": str(payload.materia_id),
                        "carrera_id": str(payload.carrera_id),
                        "cohorte_id": str(payload.cohorte_id),
                    },
                )
            await self.session.commit()

        msg = (
            f"dry_run: {afectadas} asignaciones serían afectadas."
            if payload.dry_run
            else f"Actualizadas {afectadas} asignaciones."
        )
        return ModificarVigenciaResponse(
            afectadas=afectadas,
            dry_run=payload.dry_run,
            mensaje=msg,
        )

    # ------------------------------------------------------------------
    # Export CSV (Design D4 — stdlib csv, in memory)
    # ------------------------------------------------------------------

    async def exportar_csv(
        self,
        filtros: MisEquiposFiltros,
    ) -> str:
        """
        Return CSV content as a string for equipo assignments.

        Design D4: Uses csv.DictWriter from stdlib. In-memory (StringIO).
        Columns: id, usuario_id, rol, materia_id, carrera_id, cohorte_id,
                 comisiones, desde, hasta, estado_vigencia.

        Args:
            filtros: Optional filters (same as consultar_asignaciones).

        Returns:
            CSV string (may be header-only if no assignments match).
        """
        filtros_dict = filtros.model_dump(exclude_none=True)
        asignaciones = await self.repository.listar_por_tenant(filtros=filtros_dict)

        fieldnames = [
            "id",
            "usuario_id",
            "rol",
            "materia_id",
            "carrera_id",
            "cohorte_id",
            "comisiones",
            "desde",
            "hasta",
            "estado_vigencia",
        ]

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for a in asignaciones:
            writer.writerow(
                {
                    "id": str(a.id),
                    "usuario_id": str(a.usuario_id),
                    "rol": a.rol if isinstance(a.rol, str) else a.rol.value,
                    "materia_id": str(a.materia_id) if a.materia_id else "",
                    "carrera_id": str(a.carrera_id) if a.carrera_id else "",
                    "cohorte_id": str(a.cohorte_id) if a.cohorte_id else "",
                    "comisiones": a.comisiones or "",
                    "desde": str(a.desde),
                    "hasta": str(a.hasta) if a.hasta else "",
                    "estado_vigencia": a.estado_vigencia,
                }
            )

        return output.getvalue()
