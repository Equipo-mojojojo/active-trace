from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.factura import EstadoFactura, Factura
from app.repositories.factura_repository import FacturaRepository
from app.repositories.usuario_repository import UsuarioRepository


class FacturaForbiddenError(PermissionError):
    pass


class FacturaNotFoundError(LookupError):
    pass


class FacturaConflictError(RuntimeError):
    pass


class FacturaService:
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        self.session = session
        self.tenant_id = UUID(str(tenant_id))
        self._repo = FacturaRepository(session, tenant_id)
        self._usuario_repo = UsuarioRepository(session, tenant_id)

    async def _assert_facturante(self, usuario_id: UUID) -> None:
        usuario = await self._usuario_repo.get_by_id(usuario_id)
        if usuario is None:
            raise FacturaNotFoundError("usuario_not_found")
        if not getattr(usuario, "modalidad_cobro", None) == "factura":
            raise FacturaConflictError("docente_no_facturante")

    async def crear(
        self,
        usuario_id: UUID,
        periodo: str,
        monto: Decimal,
        fecha_carga: date,
        detalle: str | None = None,
    ) -> Factura:
        await self._assert_facturante(usuario_id)
        return await self._repo.create(
            usuario_id=usuario_id,
            periodo=periodo,
            monto=monto,
            fecha_carga=fecha_carga,
            detalle=detalle,
            estado=EstadoFactura.PENDIENTE,
        )

    async def listar(
        self,
        estado: str | None = None,
        periodo: str | None = None,
        usuario_id: UUID | None = None,
    ) -> list[Factura]:
        return await self._repo.list_by_tenant(estado=estado, periodo=periodo, usuario_id=usuario_id)

    async def cambiar_estado(self, factura_id: UUID, estado: EstadoFactura) -> Factura:
        row = await self._repo.update_estado(factura_id, estado)
        if row is None:
            raise FacturaNotFoundError("factura_not_found")
        return row

    async def adjuntar_archivo(self, factura_id: UUID, archivo_path: str) -> Factura:
        row = await self._repo.update_archivo_path(factura_id, archivo_path)
        if row is None:
            raise FacturaNotFoundError("factura_not_found")
        return row
