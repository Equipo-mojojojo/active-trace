---
name: postgresql-table-design
description: Patrones de modelos SQLAlchemy 2.0 async y migraciones Alembic para active-trace. Mixins, tenant isolation, soft delete, tipos especiales.
license: MIT
---

# PostgreSQL Table Design — active-trace

## Mixins disponibles (backend/app/models/base.py)

```python
# Todos los modelos de dominio heredan de estos mixins:
class MiModelo(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, TenantMixin, Base):
    __tablename__ = "mi_tabla"
    ...

# Tenant NO lleva TenantMixin (es la raíz)
class Tenant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenant"
```

## Columnas estándar (ya incluidas por mixins)

| Mixin | Columnas |
|-------|----------|
| UUIDPrimaryKeyMixin | `id UUID PRIMARY KEY` |
| TimestampMixin | `created_at`, `updated_at` |
| SoftDeleteMixin | `deleted_at` (soft delete) |
| TenantMixin | `tenant_id UUID FK → tenant.id` |

## Definición de modelo completo

```python
from sqlalchemy import String, ForeignKey, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, TenantMixin
from app.core.security import EncryptedString
from uuid import UUID


class MiModelo(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, TenantMixin, Base):
    __tablename__ = "mi_tabla"

    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(500), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # PII — SIEMPRE cifrada
    email: Mapped[str | None] = mapped_column(EncryptedString(), nullable=True)

    # FK a otra entidad del mismo tenant
    otra_id: Mapped[UUID] = mapped_column(ForeignKey("otra_tabla.id"), nullable=False)
    otra: Mapped["OtraEntidad"] = relationship(lazy="select")
```

## Reglas de modelos

- **Soft delete siempre** — nunca `.delete()` físico; usar `mark_deleted()` del mixin
- **PII cifrada** — DNI, CUIL, CBU, email → `EncryptedString()`
- **tenant_id en toda tabla de dominio** — sin excepción
- **≤500 LOC por archivo** — si crece, partir por entidad
- **Una migración por cambio de schema**

## Template de migración Alembic

```python
"""descripcion del cambio

Revision ID: 00NN_nombre_corto          ← máx 32 chars TOTAL
Revises: 00NN-1_revision_anterior
Create Date: YYYY-MM-DD HH:MM:SS
"""
from alembic import op
import sqlalchemy as sa

revision = "00NN_nombre_corto"           # ← máx 32 chars
down_revision = "00NN-1_anterior"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mi_tabla",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mi_tabla_tenant_id", "mi_tabla", ["tenant_id"])
    op.create_index("ix_mi_tabla_deleted_at", "mi_tabla", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("ix_mi_tabla_deleted_at", "mi_tabla")
    op.drop_index("ix_mi_tabla_tenant_id", "mi_tabla")
    op.drop_table("mi_tabla")
```

## Seed data en migraciones

```python
def upgrade() -> None:
    # ... create tables ...

    # Seed solo si ya existe un tenant — NUNCA generar UUID random
    conn = op.get_bind()
    row = conn.execute(sa.text("SELECT id FROM tenant LIMIT 1")).fetchone()
    if row is None:
        return  # DB vacía — skip seed
    tenant_id = str(row[0])
    # ... insertar seed data con tenant_id real ...
```

## Índices útiles

```python
# Soft delete queries
op.create_index("ix_tabla_deleted_at", "tabla", ["deleted_at"])
# Tenant isolation
op.create_index("ix_tabla_tenant_id", "tabla", ["tenant_id"])
# Unicidad por tenant
sa.UniqueConstraint("tenant_id", "codigo", name="uq_tabla_tenant_codigo")
```

## Relaciones async — no usar lazy="dynamic"

```python
# ✅ Correcto para async
items: Mapped[list["Item"]] = relationship(lazy="select")

# ❌ No usar en async
items = relationship("Item", lazy="dynamic")
```
