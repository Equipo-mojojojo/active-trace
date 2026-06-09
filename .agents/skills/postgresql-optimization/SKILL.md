---
name: postgresql-optimization
description: Patrones de optimización PostgreSQL + SQLAlchemy 2.0 async para active-trace. Índices, N+1, paginación, JSONB, pooling.
license: MIT
---

# PostgreSQL Optimization — active-trace

## Índices — cuándo y cómo

```python
from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column

class MiModelo(Base, TenantScopedModelMixin):
    # Índice compuesto obligatorio en tablas con scope de tenant
    __table_args__ = (
        Index("ix_mi_modelo_tenant_estado", "tenant_id", "estado"),
        Index("ix_mi_modelo_tenant_created", "tenant_id", "created_at"),
    )

    estado: Mapped[str] = mapped_column(String(20), nullable=False)
```

```python
# En la migración Alembic correspondiente
def upgrade() -> None:
    op.create_index("ix_mi_modelo_tenant_estado", "mi_modelo", ["tenant_id", "estado"])
    op.create_index("ix_mi_modelo_tenant_created", "mi_modelo", ["tenant_id", "created_at"])
```

## Prevenir N+1 — eager loading

```python
from sqlalchemy.orm import selectinload, joinedload

# selectinload para colecciones (uno-a-muchos)
async def listar_con_comentarios(self) -> list[Tarea]:
    result = await self.db.execute(
        select(Tarea)
        .options(selectinload(Tarea.comentarios))
        .where(Tarea.tenant_id == self.tenant_id, Tarea.deleted_at.is_(None))
        .order_by(Tarea.created_at.desc())
    )
    return result.scalars().all()

# joinedload para relaciones muchos-a-uno (FK → objeto padre)
async def listar_asignaciones(self) -> list[Asignacion]:
    result = await self.db.execute(
        select(Asignacion)
        .options(joinedload(Asignacion.usuario), joinedload(Asignacion.materia))
        .where(Asignacion.tenant_id == self.tenant_id)
    )
    return result.scalars().unique().all()
```

## Paginación con offset/limit (estándar)

```python
async def listar_paginado(
    self,
    limit: int = 100,
    offset: int = 0,
    filtros: dict | None = None,
) -> tuple[list[MiModelo], int]:
    q = (
        select(MiModelo)
        .where(MiModelo.tenant_id == self.tenant_id, MiModelo.deleted_at.is_(None))
    )
    if filtros:
        if filtros.get("estado"):
            q = q.where(MiModelo.estado == filtros["estado"])

    total = await self.db.scalar(select(func.count()).select_from(q.subquery()))
    items = (await self.db.execute(q.offset(offset).limit(limit))).scalars().all()
    return items, total
```

## JSONB — consultas sobre campos configurables

```python
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import cast, type_coerce

class Calificacion(Base, TenantScopedModelMixin):
    detalle: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

# Filtrar por clave JSONB
async def buscar_por_actividad(self, actividad_id: str) -> list[Calificacion]:
    result = await self.db.execute(
        select(Calificacion).where(
            Calificacion.tenant_id == self.tenant_id,
            Calificacion.detalle["actividad_id"].as_string() == actividad_id,
        )
    )
    return result.scalars().all()
```

## Bulk insert — alta de registros masivos

```python
from sqlalchemy import insert

async def bulk_insert(self, items: list[dict]) -> None:
    if not items:
        return
    await self.db.execute(insert(MiModelo), items)
    await self.db.flush()
```

## Transacciones y flush vs commit

```python
# En services — usar flush (no commit). El commit lo maneja el middleware de sesión.
async def crear(self, dto: MiCreateDTO) -> MiModelo:
    entidad = MiModelo(tenant_id=self.tenant_id, **dto.model_dump())
    self.db.add(entidad)
    await self.db.flush()       # persiste en la transacción, no commitea
    await self.db.refresh(entidad)  # recarga campos generados por DB (id, timestamps)
    return entidad
```

## Connection pooling — configuración

```python
# En core/database.py — valores para active-trace
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,           # conexiones base del pool
    max_overflow=20,        # conexiones extra en pico
    pool_pre_ping=True,     # verifica conexión antes de usar
    pool_recycle=3600,      # recicla conexiones cada hora
)
```

## Explain analyze — diagnóstico

```sql
-- Para diagnosticar queries lentos, correr en psql o DBeaver:
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM mi_modelo
WHERE tenant_id = 'uuid' AND estado = 'Activo'
ORDER BY created_at DESC
LIMIT 100;
-- Buscar: Seq Scan en tablas grandes → necesita índice
-- Buscar: Nested Loop con muchas filas → considerar JOIN o subquery
```

## Reglas

- **Nunca `SELECT *`** — especificar columnas en queries explícitos
- **Siempre `deleted_at.is_(None)`** en queries de datos activos
- **Siempre `tenant_id == self.tenant_id`** — sin excepciones
- **`flush()` en services**, nunca `commit()` manual salvo en workers
- **Índices en toda FK + columnas de filtro frecuente** (estado, tenant_id, created_at)
