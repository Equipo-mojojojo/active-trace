from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guardia import Guardia
from app.repositories.guardia_repository import GuardiaRepository
from app.schemas.guardias import GuardiaCreate, GuardiaUpdate


class GuardiaService:
    """Service for managing guardias de atención.

    TUTOR: solo ve/edita sus propias guardias (scope `:propio`).
    COORDINADOR: ve/edita todas las guardias del tenant.
    """

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.repository = GuardiaRepository(db, tenant_id)
        self.db = db
        self.tenant_id = tenant_id

    async def list(
        self,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        asignacion_id: UUID | None = None,
        estado: str | None = None,
        scope_propio: bool = False,
        usuario_asignaciones: list[UUID] | None = None,
    ) -> list[Guardia]:
        """List guardias with optional filters.

        Args:
            materia_id: Filter by materia.
            carrera_id: Filter by carrera.
            cohorte_id: Filter by cohorte.
            asignacion_id: Filter by specific asignacion.
            estado: Filter by estado.
            scope_propio: If True, only return guardias where the user's
                asignacion_id is in ``usuario_asignaciones``.
            usuario_asignaciones: List of asignacion IDs belonging to
                the current user (used for scope `:propio`).
        """
        stmt = select(Guardia).where(
            Guardia.tenant_id == self.tenant_id,
            Guardia.deleted_at.is_(None),
        )

        if scope_propio and usuario_asignaciones:
            stmt = stmt.where(Guardia.asignacion_id.in_(usuario_asignaciones))
        if materia_id is not None:
            stmt = stmt.where(Guardia.materia_id == materia_id)
        if carrera_id is not None:
            stmt = stmt.where(Guardia.carrera_id == carrera_id)
        if cohorte_id is not None:
            stmt = stmt.where(Guardia.cohorte_id == cohorte_id)
        if asignacion_id is not None:
            stmt = stmt.where(Guardia.asignacion_id == asignacion_id)
        if estado is not None:
            stmt = stmt.where(Guardia.estado == estado)

        stmt = stmt.order_by(Guardia.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get(self, guardia_id: UUID) -> Guardia:
        guardia = await self.repository.get_by_id(guardia_id)
        if guardia is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guardia no encontrada",
            )
        return guardia

    async def create(self, data: GuardiaCreate) -> Guardia:
        return await self.repository.create(**data.model_dump())

    async def update(
        self, guardia_id: UUID, data: GuardiaUpdate
    ) -> Guardia:
        guardia = await self.get(guardia_id)

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return guardia

        for field, value in update_data.items():
            setattr(guardia, field, value)

        await self.db.flush()
        await self.db.refresh(guardia)
        return guardia
