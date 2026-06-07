"""
AnalisisService: Business logic for C-11 analysis and reports.

All computation is done in pure functions that receive in-memory lists.
The service orchestrates repository calls, applies filters, and delegates
computation to the pure functions below.

Design decisions applied:
  D1: Stateless computation — recalculates on each request.
  D2: Atrasado defined at student × materia level.
  D3: Ranking uses persisted aprobado field.
  D4: Notas finales = average of nota_numerica over selected activities.
  D5: Monitor scope derived from JWT role.
  D6: CSV export generated in-memory.
"""

from __future__ import annotations

import csv
import io
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.analisis_repository import AnalisisRepository

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal data structures (pure — no ORM dependency)
# ---------------------------------------------------------------------------


@dataclass
class EntradaSimple:
    id: UUID
    nombre: str
    apellidos: str
    comision: Optional[str]
    materia_id: UUID


@dataclass
class CalificacionSimple:
    entrada_padron_id: UUID
    actividad: str
    aprobado: bool
    nota_numerica: Optional[Decimal] = None
    nota_textual: Optional[str] = None


@dataclass
class AlumnoAtrasadoInternal:
    entrada_padron_id: UUID
    nombre: str
    apellidos: str
    comision: Optional[str]
    materia_id: UUID
    actividades_faltantes: list[str] = field(default_factory=list)
    actividades_reprobadas: list[str] = field(default_factory=list)


@dataclass
class RankingEntryInternal:
    entrada_padron_id: UUID
    aprobadas: int


@dataclass
class NotaFinalInternal:
    entrada_padron_id: UUID
    nombre: str
    apellidos: str
    nota_final: Decimal


@dataclass
class ActividadMetricaInternal:
    actividad: str
    total: int
    aprobadas: int

    @property
    def tasa_aprobacion(self) -> float:
        return self.aprobadas / self.total if self.total else 0.0


@dataclass
class ReporteRapidoInternal:
    materia_id: UUID
    total_alumnos: int
    con_aprobadas: int
    atrasados: int
    actividades: list[ActividadMetricaInternal]


# ---------------------------------------------------------------------------
# Pure computation functions
# ---------------------------------------------------------------------------


def computar_atrasados(
    entradas: list[EntradaSimple],
    calificaciones: list[CalificacionSimple],
) -> list[AlumnoAtrasadoInternal]:
    """Classify students as atrasado per RN-06.

    A student is atrasado if:
    - has at least one Calificacion with aprobado=False (reprobada), OR
    - is missing an activity that exists for other students in the same materia.

    If no calificaciones exist for any student, there are no known activities
    and nobody is atrasado.
    """
    if not calificaciones:
        return []

    # Known activities across all students
    todas_actividades: set[str] = {c.actividad for c in calificaciones}

    # Index: entrada_padron_id → set of actividades with calificacion
    cal_por_alumno: dict[UUID, dict[str, bool]] = defaultdict(dict)
    for c in calificaciones:
        cal_por_alumno[c.entrada_padron_id][c.actividad] = c.aprobado

    resultado: list[AlumnoAtrasadoInternal] = []

    for entrada in entradas:
        mis_cals = cal_por_alumno.get(entrada.id, {})
        faltantes = sorted(todas_actividades - mis_cals.keys())
        reprobadas = sorted(act for act, aprobado in mis_cals.items() if not aprobado)

        if faltantes or reprobadas:
            resultado.append(
                AlumnoAtrasadoInternal(
                    entrada_padron_id=entrada.id,
                    nombre=entrada.nombre,
                    apellidos=entrada.apellidos,
                    comision=entrada.comision,
                    materia_id=entrada.materia_id,
                    actividades_faltantes=faltantes,
                    actividades_reprobadas=reprobadas,
                )
            )

    return resultado


def computar_ranking(
    calificaciones: list[CalificacionSimple],
) -> list[RankingEntryInternal]:
    """Compute ranking of approved activities per student (RN-09).

    Only students with ≥1 approved activity appear. Ordered descending.
    """
    conteo: dict[UUID, int] = defaultdict(int)
    for c in calificaciones:
        if c.aprobado:
            conteo[c.entrada_padron_id] += 1

    ranking = [
        RankingEntryInternal(entrada_padron_id=ep_id, aprobadas=count)
        for ep_id, count in conteo.items()
        if count > 0
    ]
    ranking.sort(key=lambda r: r.aprobadas, reverse=True)
    return ranking


def computar_notas_finales(
    entradas: list[EntradaSimple],
    calificaciones: list[CalificacionSimple],
    actividades_seleccionadas: list[str],
) -> list[NotaFinalInternal]:
    """Compute final grade (average nota_numerica) for selected activities (F2.5).

    Students with no numeric grades for any selected activity are omitted.
    """
    sel = set(actividades_seleccionadas)
    notas_por_alumno: dict[UUID, list[Decimal]] = defaultdict(list)

    for c in calificaciones:
        if c.actividad in sel and c.nota_numerica is not None:
            notas_por_alumno[c.entrada_padron_id].append(c.nota_numerica)

    entrada_map = {e.id: e for e in entradas}
    resultado: list[NotaFinalInternal] = []

    for ep_id, notas in notas_por_alumno.items():
        if not notas:
            continue
        promedio = sum(notas) / len(notas)
        promedio = promedio.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        entrada = entrada_map.get(ep_id)
        nombre = entrada.nombre if entrada else ""
        apellidos = entrada.apellidos if entrada else ""
        resultado.append(
            NotaFinalInternal(
                entrada_padron_id=ep_id,
                nombre=nombre,
                apellidos=apellidos,
                nota_final=promedio,
            )
        )

    resultado.sort(key=lambda r: r.nota_final, reverse=True)
    return resultado


def computar_reporte_rapido(
    entradas: list[EntradaSimple],
    calificaciones: list[CalificacionSimple],
    materia_id: UUID,
) -> ReporteRapidoInternal:
    """Compute fast materia report (F2.4)."""
    atrasados = computar_atrasados(entradas, calificaciones)
    atrasados_ids = {a.entrada_padron_id for a in atrasados}

    # Students with ≥1 approved
    aprobadas_por_alumno: dict[UUID, int] = defaultdict(int)
    for c in calificaciones:
        if c.aprobado:
            aprobadas_por_alumno[c.entrada_padron_id] += 1
    con_aprobadas = sum(1 for v in aprobadas_por_alumno.values() if v > 0)

    # Activity metrics
    total_por_actividad: dict[str, int] = defaultdict(int)
    aprobadas_por_actividad: dict[str, int] = defaultdict(int)
    for c in calificaciones:
        total_por_actividad[c.actividad] += 1
        if c.aprobado:
            aprobadas_por_actividad[c.actividad] += 1

    actividades_metricas = [
        ActividadMetricaInternal(
            actividad=act,
            total=total_por_actividad[act],
            aprobadas=aprobadas_por_actividad.get(act, 0),
        )
        for act in total_por_actividad
    ]
    actividades_metricas.sort(key=lambda a: a.tasa_aprobacion)

    return ReporteRapidoInternal(
        materia_id=materia_id,
        total_alumnos=len(entradas),
        con_aprobadas=con_aprobadas,
        atrasados=len(atrasados_ids),
        actividades=actividades_metricas,
    )


# ---------------------------------------------------------------------------
# AnalisisService — orchestrates repo + pure functions
# ---------------------------------------------------------------------------


class AnalisisService:
    """Orchestrates data fetching and analysis computation for C-11."""

    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        self.tenant_id = UUID(str(tenant_id))
        self.repo = AnalisisRepository(session, tenant_id)

    def _to_entradas(self, rows) -> list[EntradaSimple]:
        entradas: list[EntradaSimple] = []
        for row in rows:
            materia_id = getattr(
                row, "_trace_materia_id", getattr(row, "materia_id", None)
            )
            if materia_id is None:
                raise ValueError("EntradaPadron row missing materia_id context")
            entradas.append(
                EntradaSimple(
                    id=row.id,
                    nombre=row.nombre,
                    apellidos=row.apellidos,
                    comision=row.comision,
                    materia_id=materia_id,
                )
            )
        return entradas

    def _to_calificaciones(self, rows) -> list[CalificacionSimple]:
        return [
            CalificacionSimple(
                entrada_padron_id=r.entrada_padron_id,
                actividad=r.actividad,
                aprobado=r.aprobado,
                nota_numerica=r.nota_numerica,
                nota_textual=r.nota_textual,
            )
            for r in rows
        ]

    async def obtener_atrasados(
        self,
        materia_id: UUID,
        cohorte_id: Optional[UUID] = None,
        comision: Optional[str] = None,
    ) -> dict:
        entradas_orm = await self.repo.entradas_por_materia(materia_id)
        if comision:
            entradas_orm = [e for e in entradas_orm if e.comision == comision]

        cals_orm = await self.repo.calificaciones_por_materia(materia_id)
        entradas = self._to_entradas(entradas_orm)
        cals = self._to_calificaciones(cals_orm)

        atrasados = computar_atrasados(entradas, cals)
        return {
            "total": len(atrasados),
            "atrasados": [
                {
                    "entrada_padron_id": str(a.entrada_padron_id),
                    "nombre": a.nombre,
                    "apellidos": a.apellidos,
                    "comision": a.comision,
                    "materia_id": str(a.materia_id),
                    "actividades_faltantes": a.actividades_faltantes,
                    "actividades_reprobadas": a.actividades_reprobadas,
                }
                for a in atrasados
            ],
        }

    async def obtener_ranking(self, materia_id: UUID) -> dict:
        entradas_orm = await self.repo.entradas_por_materia(materia_id)
        cals_orm = await self.repo.calificaciones_por_materia(materia_id)
        entrada_map = {e.id: e for e in entradas_orm}
        cals = self._to_calificaciones(cals_orm)

        ranking = computar_ranking(cals)
        return {
            "total": len(ranking),
            "ranking": [
                {
                    "entrada_padron_id": str(r.entrada_padron_id),
                    "nombre": entrada_map[r.entrada_padron_id].nombre
                    if r.entrada_padron_id in entrada_map
                    else "",
                    "apellidos": entrada_map[r.entrada_padron_id].apellidos
                    if r.entrada_padron_id in entrada_map
                    else "",
                    "comision": entrada_map[r.entrada_padron_id].comision
                    if r.entrada_padron_id in entrada_map
                    else None,
                    "aprobadas": r.aprobadas,
                }
                for r in ranking
            ],
        }

    async def obtener_reporte(self, materia_id: UUID) -> dict:
        entradas_orm = await self.repo.entradas_por_materia(materia_id)
        cals_orm = await self.repo.calificaciones_por_materia(materia_id)
        entradas = self._to_entradas(entradas_orm)
        cals = self._to_calificaciones(cals_orm)

        reporte = computar_reporte_rapido(entradas, cals, materia_id)
        return {
            "materia_id": str(reporte.materia_id),
            "total_alumnos": reporte.total_alumnos,
            "con_aprobadas": reporte.con_aprobadas,
            "atrasados": reporte.atrasados,
            "actividades": [
                {
                    "actividad": a.actividad,
                    "total": a.total,
                    "aprobadas": a.aprobadas,
                    "tasa_aprobacion": round(a.tasa_aprobacion, 4),
                }
                for a in reporte.actividades
            ],
        }

    async def obtener_notas_finales(
        self, materia_id: UUID, actividades_seleccionadas: list[str]
    ) -> dict:
        entradas_orm = await self.repo.entradas_por_materia(materia_id)
        cals_orm = await self.repo.calificaciones_por_materia(materia_id)
        entradas = self._to_entradas(entradas_orm)
        cals = self._to_calificaciones(cals_orm)

        notas = computar_notas_finales(entradas, cals, actividades_seleccionadas)
        return {
            "actividades_seleccionadas": actividades_seleccionadas,
            "notas": [
                {
                    "entrada_padron_id": str(n.entrada_padron_id),
                    "nombre": n.nombre,
                    "apellidos": n.apellidos,
                    "nota_final": str(n.nota_final),
                }
                for n in notas
            ],
        }

    async def obtener_monitor(
        self,
        actor,
        materia_id: Optional[UUID] = None,
        comision: Optional[str] = None,
        regional: Optional[str] = None,
        q: Optional[str] = None,
        min_aprobadas: Optional[int] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> dict:
        """Monitor endpoint with role-based scope (D5)."""
        actor_roles = [r.nombre for r in getattr(actor, "roles", [])]
        is_coord_or_admin = "COORDINADOR" in actor_roles or "ADMIN" in actor_roles

        # Determine which materias this actor can see
        if is_coord_or_admin:
            entradas_orm = await self.repo.todas_las_entradas()
        else:
            asignaciones = await self.repo.asignaciones_activas_usuario(actor.id)
            materia_ids = {a.materia_id for a in asignaciones}
            if not materia_ids:
                return {"total": 0, "limit": limit, "offset": offset, "entries": []}
            # Fetch all entradas for those materias
            all_entradas = []
            for mid in materia_ids:
                rows = await self.repo.entradas_por_materia(mid)
                all_entradas.extend(rows)
            entradas_orm = all_entradas

        # Apply materia filter
        if materia_id:
            entradas_orm = [
                e
                for e in entradas_orm
                if getattr(e, "_trace_materia_id", getattr(e, "materia_id", None))
                == materia_id
            ]
        if comision:
            entradas_orm = [e for e in entradas_orm if e.comision == comision]
        if regional:
            entradas_orm = [
                e for e in entradas_orm if getattr(e, "regional", None) == regional
            ]
        if q:
            q_lower = q.lower()
            entradas_orm = [
                e
                for e in entradas_orm
                if q_lower in e.nombre.lower()
                or q_lower in e.apellidos.lower()
                or q_lower in (getattr(e, "email", "") or "").lower()
            ]

        # Fetch calificaciones for the filtered entradas
        entry_ids = [e.id for e in entradas_orm]
        cals_orm = await self.repo.calificaciones_por_entradas(entry_ids)

        # Apply date range filter (COORDINADOR/ADMIN only, D5)
        if is_coord_or_admin and (fecha_desde or fecha_hasta):
            filtered_cals = []
            for c in cals_orm:
                imp_at = getattr(c, "importado_at", None)
                if imp_at:
                    imp_date = imp_at.date() if hasattr(imp_at, "date") else imp_at
                    if fecha_desde and imp_date < fecha_desde:
                        continue
                    if fecha_hasta and imp_date > fecha_hasta:
                        continue
                filtered_cals.append(c)
            cals_orm = filtered_cals

        # Build monitor entries
        todas_actividades: set[str] = {c.actividad for c in cals_orm}
        cal_por_alumno: dict[UUID, dict[str, bool]] = defaultdict(dict)
        for c in cals_orm:
            cal_por_alumno[c.entrada_padron_id][c.actividad] = c.aprobado

        entries = []
        for entrada in entradas_orm:
            mis = cal_por_alumno.get(entrada.id, {})
            aprobadas = sum(1 for v in mis.values() if v)
            reprobadas = sum(1 for v in mis.values() if not v)
            faltantes = len(todas_actividades - mis.keys())
            atrasado = bool(reprobadas or faltantes) and bool(todas_actividades)

            if min_aprobadas is not None and aprobadas < min_aprobadas:
                continue

            entries.append(
                {
                    "entrada_padron_id": str(entrada.id),
                    "nombre": entrada.nombre,
                    "apellidos": entrada.apellidos,
                    "comision": entrada.comision,
                    "regional": getattr(entrada, "regional", None),
                    "materia_id": str(
                        getattr(
                            entrada,
                            "_trace_materia_id",
                            getattr(entrada, "materia_id", None),
                        )
                    ),
                    "aprobadas": aprobadas,
                    "reprobadas": reprobadas,
                    "faltantes": faltantes,
                    "atrasado": atrasado,
                }
            )

        total = len(entries)
        paginated = entries[offset : offset + limit]
        return {"total": total, "limit": limit, "offset": offset, "entries": paginated}

    async def export_sin_corregir_csv(self, materia_id: UUID) -> str:
        """Generate CSV of ungraded textual activities (RN-07, RN-08) — in-memory."""
        entradas_orm = await self.repo.entradas_por_materia(materia_id)
        cals_orm = await self.repo.calificaciones_por_materia(materia_id)

        # Determine textual activities (not numeric)
        textual_actividades = {
            c.actividad
            for c in cals_orm
            if not c.actividad.strip().lower().endswith("(real)")
            and c.nota_textual is not None
        }
        all_actividades = {c.actividad for c in cals_orm}
        # Also include activities where some students have no nota_textual at all
        # We need activities that are textual in nature
        from app.services.calificaciones_parser import TEXTUAL_SCALE_VALUES

        textual_by_value = {
            c.actividad
            for c in cals_orm
            if c.nota_textual and c.nota_textual.lower() in TEXTUAL_SCALE_VALUES
        }
        textual_actividades = textual_actividades | textual_by_value

        # Graded set: (entrada_padron_id, actividad) with nota_textual
        graded = {
            (c.entrada_padron_id, c.actividad)
            for c in cals_orm
            if c.nota_textual is not None
        }

        # Activities present in finalizacion context — use all textual ones known
        entrada_map = {e.id: e for e in entradas_orm}
        rows: list[dict] = []
        for c in cals_orm:
            if c.actividad not in textual_actividades:
                continue
            if (c.entrada_padron_id, c.actividad) not in graded:
                entrada = entrada_map.get(c.entrada_padron_id)
                if entrada:
                    rows.append(
                        {
                            "nombre": entrada.nombre,
                            "apellidos": entrada.apellidos,
                            "comision": entrada.comision or "",
                            "actividad": c.actividad,
                        }
                    )

        buf = io.StringIO()
        writer = csv.DictWriter(
            buf, fieldnames=["nombre", "apellidos", "comision", "actividad"]
        )
        writer.writeheader()
        writer.writerows(rows)
        return buf.getvalue()
