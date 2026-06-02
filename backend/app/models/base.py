from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UUIDPrimaryKeyMixin:
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    def mark_deleted(self) -> None:
        self.deleted_at = utc_now()


class BaseModelMixin(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    pass


class TenantScopedModelMixin(BaseModelMixin):
    @declared_attr.directive
    def tenant_id(cls) -> Mapped[UUID]:
        return mapped_column(Uuid, ForeignKey("tenant.id"), nullable=False, index=True)
