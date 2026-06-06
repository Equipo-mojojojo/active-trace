from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import BaseModelMixin


class Tenant(Base, BaseModelMixin):
    __tablename__ = "tenant"

    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    communication_approval_required: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )
