from __future__ import annotations

from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base
from app.core.tenancy import TenantScopeError, normalize_tenant_id

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Base repository primitives shared by persistence helpers."""

    def __init__(self, session: AsyncSession, model: type[ModelT]):
        self.session = session
        self.model = model


class TenantScopedRepository(BaseRepository[ModelT]):
    """Repository that enforces tenant isolation and soft delete defaults.

    `include_deleted=True` is the explicit escape hatch for historical/audit reads.
    """

    def __init__(
        self,
        session: AsyncSession,
        model: type[ModelT],
        tenant_id: UUID | str,
    ):
        super().__init__(session, model)
        self.tenant_id = normalize_tenant_id(tenant_id)

    def _statement(self, include_deleted: bool = False) -> Select[tuple[ModelT]]:
        statement = select(self.model).where(self.model.tenant_id == self.tenant_id)

        if hasattr(self.model, "deleted_at") and not include_deleted:
            statement = statement.where(self.model.deleted_at.is_(None))

        return statement

    async def create(self, **values) -> ModelT:
        provided_tenant_id = values.get("tenant_id")

        if (
            provided_tenant_id is not None
            and normalize_tenant_id(provided_tenant_id) != self.tenant_id
        ):
            raise TenantScopeError(
                "Attempted to create a record outside the active tenant scope"
            )

        values["tenant_id"] = self.tenant_id
        instance = self.model(**values)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def get_by_id(
        self, record_id: UUID, include_deleted: bool = False
    ) -> ModelT | None:
        result = await self.session.execute(
            self._statement(include_deleted=include_deleted).where(
                self.model.id == record_id
            )
        )
        return result.scalar_one_or_none()

    async def list_all(self, include_deleted: bool = False) -> list[ModelT]:
        result = await self.session.execute(
            self._statement(include_deleted=include_deleted)
        )
        return list(result.scalars().all())

    async def soft_delete(self, record_id: UUID) -> ModelT | None:
        instance = await self.get_by_id(record_id)
        if instance is None:
            return None

        instance.mark_deleted()
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
