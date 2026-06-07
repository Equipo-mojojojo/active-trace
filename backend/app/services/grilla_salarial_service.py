from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.salario_base import SalarioBase
from app.models.salario_plus import SalarioPlus
from app.repositories.salario_base_repository import SalarioBaseRepository
from app.repositories.salario_plus_repository import SalarioPlusRepository


class GrillaSalarialConflictError(RuntimeError):
    pass


class GrillaSalarialService:
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        self.session = session
        self.tenant_id = UUID(str(tenant_id))
        self._base_repo = SalarioBaseRepository(session, tenant_id)
        self._plus_repo = SalarioPlusRepository(session, tenant_id)

    async def crear_base(
        self, rol: str, monto: Decimal, desde: date, hasta: date | None = None
    ) -> SalarioBase:
        try:
            return await self._base_repo.create_base(rol, monto, desde, hasta)
        except ValueError as exc:
            raise GrillaSalarialConflictError(str(exc)) from exc

    async def listar_base(self) -> list[SalarioBase]:
        return await self._base_repo.list_by_tenant()

    async def actualizar_base(self, record_id: UUID, **values) -> SalarioBase | None:
        try:
            return await self._base_repo.update(record_id, **values)
        except ValueError as exc:
            raise GrillaSalarialConflictError(str(exc)) from exc

    async def crear_plus(
        self,
        grupo: str,
        rol: str,
        descripcion: str,
        monto: Decimal,
        desde: date,
        hasta: date | None = None,
    ) -> SalarioPlus:
        try:
            return await self._plus_repo.create_plus(grupo, rol, descripcion, monto, desde, hasta)
        except ValueError as exc:
            raise GrillaSalarialConflictError(str(exc)) from exc

    async def listar_plus(
        self, grupo: str | None = None, rol: str | None = None
    ) -> list[SalarioPlus]:
        return await self._plus_repo.list_by_tenant(grupo=grupo, rol=rol)

    async def actualizar_plus(self, record_id: UUID, **values) -> SalarioPlus | None:
        try:
            return await self._plus_repo.update(record_id, **values)
        except ValueError as exc:
            raise GrillaSalarialConflictError(str(exc)) from exc
