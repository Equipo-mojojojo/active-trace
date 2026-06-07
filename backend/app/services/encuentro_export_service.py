from __future__ import annotations

from datetime import date
from html import escape
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.materia import Materia
from app.repositories.materia_repository import MateriaRepository
from app.schemas.encuentros import EncuentroExportLMS
from app.services.instancia_encuentro_service import (
    InstanciaEncuentroService,
)


class EncuentroExportService:
    """Service for generating LMS-ready HTML blocks from encuentros.

    Produces a formatted HTML table with the schedule of encounters
    for a given materia, ready to embed in the virtual classroom.
    """

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.instancia_service = InstanciaEncuentroService(db, tenant_id)
        self.materia_repository = MateriaRepository(db, tenant_id)

    async def generate_html(self, materia_id: UUID) -> EncuentroExportLMS:
        """Generate HTML block for a materia's encounter schedule."""
        materia = await self.materia_repository.get_by_id(materia_id)
        materia_nombre = materia.nombre if materia else "Materia"

        instancias = await self.instancia_service.list_by_materia(materia_id)

        if not instancias:
            html = (
                f"<div class='alert alert-info'>"
                f"No hay encuentros programados para {escape(materia_nombre)}"
                f"</div>"
            )
            return EncuentroExportLMS(
                materia_nombre=materia_nombre, html=html
            )

        rows = []
        for inst in instancias:
            meet_link = (
                f"<a href='{escape(inst.meet_url)}' target='_blank'>"
                f"Enlace meet</a>"
                if inst.meet_url
                else "—"
            )
            video_link = (
                f"<a href='{escape(inst.video_url)}' target='_blank'>"
                f"Ver grabación</a>"
                if inst.video_url
                else "—"
            )
            estado_label = {
                "Programado": "🟡 Programado",
                "Realizado": "✅ Realizado",
                "Cancelado": "❌ Cancelado",
            }.get(inst.estado, inst.estado)

            rows.append(
                f"<tr>"
                f"<td>{escape(str(inst.fecha))}</td>"
                f"<td>{escape(str(inst.hora))}</td>"
                f"<td>{escape(inst.titulo)}</td>"
                f"<td>{meet_link}</td>"
                f"<td>{video_link}</td>"
                f"<td>{estado_label}</td>"
                f"</tr>"
            )

        html = (
            f"<h3>Calendario de encuentros — {escape(materia_nombre)}</h3>"
            f"<table border='1' cellpadding='8' cellspacing='0' "
            f"style='border-collapse: collapse; width: 100%;'>"
            f"<thead><tr>"
            f"<th>Fecha</th><th>Horario</th><th>Título</th>"
            f"<th>Enlace meet</th><th>Grabación</th><th>Estado</th>"
            f"</tr></thead>"
            f"<tbody>{''.join(rows)}</tbody>"
            f"</table>"
        )

        return EncuentroExportLMS(
            materia_nombre=materia_nombre, html=html
        )
