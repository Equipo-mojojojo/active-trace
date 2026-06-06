from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import EncryptedString
from app.models.base import TenantScopedModelMixin


class TenantScopedFixtureModel(Base, TenantScopedModelMixin):
    __tablename__ = "tenant_scoped_fixture_model"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    secret_value: Mapped[str | None] = mapped_column(EncryptedString(), nullable=True)
