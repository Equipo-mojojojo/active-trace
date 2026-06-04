"""
CalificacionesService: business logic for C-10 calificaciones-y-umbral.

Design decisions applied:
  D1: aprobado computed on write using active UmbralMateria.
  D2: upsert scope (tenant_id, entrada_padron_id, actividad).
  D3: UmbralMateria tied to Asignacion.
  D4: preview endpoint is stateless (no writes).
  D5: numeric columns detected by (Real) suffix.
  D6: textual approved values from UmbralMateria or defaults.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_constants import AuditAction
from app.models.calificacion import DEFAULT_UMBRAL_PCT, DEFAULT_VALORES_APROBATORIOS
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.calificaciones_repository import (
    CalificacionesRepository,
    UmbralMateriaRepository,
)
from app.services.audit_service import AuditService  # noqa: F401 — re-exported for router
from app.services.calificaciones_parser import (
    ActividadDetectada,
    CalificacionExistente,
    CalificacionRaw,
    PadronMapEntry,
    parse_calificaciones_file,
    parse_filas,
    parse_finalizacion,
    detectar_actividades,
)

logger = logging.getLogger(__name__)


class CalificacionesForbiddenError(PermissionError):
    """Raised when a user attempts an operation outside their assignment scope."""


class CalificacionesNotFoundError(LookupError):
    """Raised when a required resource (asignacion, etc.) is not found."""


def derivar_aprobado(
    nota_numerica: Decimal | None,
    nota_textual: str | None,
    umbral_pct: int,
    valores_aprobatorios: list[str],
) -> bool:
    """Compute the aprobado flag from grade data (D1 — pure function).

    Rules (spec: calificaciones-model):
    - If nota_numerica is present: compare against umbral_pct (numeric wins).
    - Else if nota_textual is present: check against valores_aprobatorios.
    - Else: False.
    """
    if nota_numerica is not None:
        return nota_numerica >= Decimal(str(umbral_pct))
    if nota_textual is not None:
        return nota_textual in valores_aprobatorios
    return False


def _resolve_umbral(umbral_pct: int | None, valores: list[str] | None) -> tuple[int, list[str]]:
    """Apply defaults when UmbralMateria is absent."""
    pct = umbral_pct if umbral_pct is not None else DEFAULT_UMBRAL_PCT
    vals = valores if valores else DEFAULT_VALORES_APROBATORIOS
    return pct, vals


class CalificacionesService:
    """Orchestrates parser, repository, and audit for calificaciones operations."""

    def __init__(
        self,
        session: AsyncSession,
        tenant_id: UUID | str,
        audit: AuditService | None = None,
    ):
        self.session = session
        self.tenant_id = UUID(str(tenant_id))
        self.cal_repo = CalificacionesRepository(session, tenant_id)
        self.umbral_repo = UmbralMateriaRepository(session, tenant_id)
        self.asig_repo = AsignacionRepository(session, tenant_id)
        self._audit = audit

    async def preview_importacion(
        self,
        file_bytes: bytes,
        filename: str,
        materia_id: UUID,
    ) -> dict:
        """Parse the LMS file and return detected activities WITHOUT writing (D4)."""
        import pandas as pd

        df = parse_calificaciones_file(file_bytes, filename)
        actividades = detectar_actividades(df)
        return {
            "actividades": [
                {
                    "nombre": a.nombre,
                    "tipo": a.tipo,
                    "muestra_valores": a.muestra_valores[:5],
                }
                for a in actividades
            ]
        }

    async def importar(
        self,
        file_bytes: bytes,
        filename: str,
        materia_id: UUID,
        actividades_seleccionadas: list[str],
        actor: object,
        asignacion_id: UUID | None = None,
    ) -> dict:
        """Parse, derive aprobado, upsert, audit. Returns count of imported rows."""
        import pandas as pd
        from app.repositories.padron_repository import PadronRepository
        from sqlalchemy import select
        from app.models.padron import EntradaPadron

        df = parse_calificaciones_file(file_bytes, filename)
        todas_actividades = detectar_actividades(df)
        actividades_sel = [
            a for a in todas_actividades if a.nombre in set(actividades_seleccionadas)
        ]

        # Resolve threshold for this actor's assignment
        umbral_pct = DEFAULT_UMBRAL_PCT
        valores_aprobatorios = list(DEFAULT_VALORES_APROBATORIOS)
        if asignacion_id:
            umbral = await self.umbral_repo.obtener_por_asignacion(asignacion_id)
            if umbral:
                umbral_pct, valores_aprobatorios = _resolve_umbral(
                    umbral.umbral_pct, umbral.valores_aprobatorios
                )

        # Build nombre_completo → entrada_padron_id map from active padron
        stmt = select(EntradaPadron).where(
            EntradaPadron.tenant_id == self.tenant_id,
            EntradaPadron.materia_id == materia_id,
            EntradaPadron.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        entradas = result.scalars().all()
        entry_map: dict[str, UUID] = {
            f"{e.nombre} {e.apellidos}": e.id for e in entradas
        }

        filas = parse_filas(df, actividades_sel, entry_map)

        count = 0
        for fila in filas:
            aprobado = derivar_aprobado(
                fila.nota_numerica, fila.nota_textual, umbral_pct, valores_aprobatorios
            )
            await self.cal_repo.upsert(
                entrada_padron_id=fila.entrada_padron_id,
                materia_id=materia_id,
                actividad=fila.actividad,
                nota_numerica=fila.nota_numerica,
                nota_textual=fila.nota_textual,
                aprobado=aprobado,
                origen="Importado",
            )
            count += 1

        if self._audit:
            await self._audit.register(
                actor_id=actor.id,
                accion=AuditAction.CALIFICACIONES_IMPORTAR,
                materia_id=materia_id,
                detalle={"filas_importadas": count},
            )

        return {"importadas": count}

    async def configurar_umbral(
        self,
        asignacion_id: UUID,
        materia_id: UUID,
        umbral_pct: int,
        valores_aprobatorios: list[str],
        actor: object,
    ) -> dict:
        """Create or update UmbralMateria for the given assignment.

        Enforces ownership: PROFESOR can only touch their own assignment.
        COORDINADOR/ADMIN can touch any assignment in the tenant.
        """
        asignacion = await self.asig_repo.get_by_id(asignacion_id)
        if asignacion is None:
            raise CalificacionesNotFoundError(f"Asignacion {asignacion_id} not found")

        # Check ownership for PROFESOR role
        actor_roles = [r.nombre for r in getattr(actor, "roles", [])]
        if "PROFESOR" in actor_roles and "COORDINADOR" not in actor_roles and "ADMIN" not in actor_roles:
            if str(asignacion.usuario_id) != str(actor.id):
                raise CalificacionesForbiddenError(
                    "PROFESOR can only configure threshold for their own assignment"
                )

        umbral = await self.umbral_repo.crear_o_actualizar(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            umbral_pct=umbral_pct,
            valores_aprobatorios=valores_aprobatorios,
        )
        return {
            "id": str(umbral.id),
            "asignacion_id": str(umbral.asignacion_id),
            "umbral_pct": umbral.umbral_pct,
            "valores_aprobatorios": umbral.valores_aprobatorios,
        }

    async def preview_finalizacion(
        self,
        file_bytes: bytes,
        filename: str,
        materia_id: UUID,
    ) -> dict:
        """Parse LMS completion report; return ungraded textual entries (no writes)."""
        from sqlalchemy import select
        from app.models.padron import EntradaPadron
        from app.models.calificacion import Calificacion

        df = parse_calificaciones_file(file_bytes, filename)

        # Build entry map
        stmt = select(EntradaPadron).where(
            EntradaPadron.tenant_id == self.tenant_id,
            EntradaPadron.materia_id == materia_id,
            EntradaPadron.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        entradas = result.scalars().all()
        entry_map: dict[str, UUID] = {
            f"{e.nombre} {e.apellidos}": e.id for e in entradas
        }

        # Determine which activities are textual (non-numeric)
        todas = detectar_actividades(df)
        textual_activities = {a.nombre for a in todas if a.tipo == "textual"}

        # Fetch existing calificaciones for these entries and materia
        entry_ids = list(entry_map.values())
        if entry_ids:
            stmt2 = select(Calificacion).where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.materia_id == materia_id,
                Calificacion.entrada_padron_id.in_(entry_ids),
                Calificacion.nota_textual.isnot(None),
                Calificacion.deleted_at.is_(None),
            )
            result2 = await self.session.execute(stmt2)
            existing_cals = [
                CalificacionExistente(
                    entrada_padron_id=c.entrada_padron_id, actividad=c.actividad
                )
                for c in result2.scalars().all()
            ]
        else:
            existing_cals = []

        pendientes = parse_finalizacion(df, entry_map, existing_cals, textual_activities)
        return {
            "pendientes": [
                {
                    "entrada_padron_id": str(p.entrada_padron_id),
                    "actividad": p.actividad,
                }
                for p in pendientes
            ]
        }
