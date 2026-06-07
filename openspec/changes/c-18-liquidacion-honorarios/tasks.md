## 1. Enums y modelos ORM

- [ ] 1.1 Agregar `EstadoLiquidacion` (Abierta/Cerrada) y `EstadoFactura` (Pendiente/Abonada) en `app/models/enums.py`
- [ ] 1.2 Crear modelo `GrupoMateria` en `app/models/grupo_materia.py` con `TenantScopedModelMixin`, columnas `clave` (varchar, unique por tenant), `descripcion`, UNIQUE `(tenant_id, clave)`
- [ ] 1.3 Agregar FK `grupo_materia_id` nullable al modelo `Materia` existente en `app/models/materia.py` — FK → `GrupoMateria.id`
- [ ] 1.4 Crear modelo `SalarioBase` en `app/models/salario_base.py` con `TenantScopedModelMixin`, columnas `rol`, `monto` (Numeric), `desde`, `hasta`, y UNIQUE constraint `(tenant_id, rol, desde)`
- [ ] 1.5 Crear modelo `SalarioPlus` en `app/models/salario_plus.py` con `TenantScopedModelMixin`, columnas `grupo_id` (FK → GrupoMateria.id), `rol`, `descripcion`, `monto` (Numeric), `desde`, `hasta`, y UNIQUE constraint `(tenant_id, grupo_id, rol, desde)`
- [ ] 1.6 Crear modelo `Liquidacion` en `app/models/liquidacion.py` con `UUIDPrimaryKeyMixin`, `TimestampMixin` y `tenant_id` declarado (sin soft delete), FK a `Cohorte` y `Usuario`, columnas `periodo`, `rol`, `comisiones` (JSON list), `monto_base`, `monto_plus`, `total` (Numeric), `es_nexo`, `excluido_por_factura`, `estado` (EstadoLiquidacion), UNIQUE constraint `(tenant_id, cohorte_id, periodo, usuario_id)`
- [ ] 1.7 Crear modelo `Factura` en `app/models/factura.py` con `UUIDPrimaryKeyMixin`, `TimestampMixin` y `tenant_id` declarado (sin soft delete), FK a `Usuario`, columnas `periodo`, `detalle`, `referencia_archivo`, `tamano_kb` (Numeric), `estado` (EstadoFactura), `cargada_at`, `abonada_at`
- [ ] 1.8 Exportar los 5 modelos en `app/models/__init__.py`

## 2. Migración Alembic

- [ ] 2.1 Generar revisión Alembic con `alembic revision -m "create liquidaciones y honorarios" --rev-id <next>`
- [ ] 2.2 Implementar `upgrade()`: crear tabla `grupo_materia`, luego ALTER TABLE `materia` agregando FK `grupo_materia_id`, luego `salario_base`, luego `salario_plus` con FK a `grupo_materia`, luego `liquidacion`, luego `factura`
- [ ] 2.3 Implementar `downgrade()`: eliminar tablas en orden inverso (factura → liquidacion → salario_plus → salario_base → revertir FK en materia → grupo_materia)
- [ ] 2.4 Verificar migración con `alembic upgrade head` y `alembic downgrade -1` en base local

## 3. Schemas Pydantic

- [ ] 3.1 Crear `schemas/liquidacion_schema.py` con:
  - `SalarioBaseCreate`, `SalarioBaseUpdate`, `SalarioBaseResponse`
  - `SalarioPlusCreate`, `SalarioPlusUpdate`, `SalarioPlusResponse`
  - `LiquidacionResponse`, `LiquidacionKPIResponse`
  - `FacturaCreate`, `FacturaUpdate`, `FacturaResponse`
  - Todos los Create/Update con `ConfigDict(extra="forbid")` y Response con `ConfigDict(from_attributes=True)`
- [ ] 3.2 Exportar schemas en `app/schemas/__init__.py`

## 4. Repositorios

- [ ] 4.1 Crear `repositories/grupo_materia_repository.py` con `TenantScopedRepository[GrupoMateria]` (CRUD heredado suficiente)
- [ ] 4.2 Crear `repositories/salario_base_repository.py` con `TenantScopedRepository[SalarioBase]` y método `find_vigente(rol, periodo) -> SalarioBase | None`
- [ ] 4.3 Crear `repositories/salario_plus_repository.py` con `TenantScopedRepository[SalarioPlus]` y método `list_vigentes(periodo) -> list[SalarioPlus]`
- [ ] 4.4 Crear `repositories/liquidacion_repository.py` con `TenantScopedRepository[Liquidacion]` y métodos: `find_by_cohorte_periodo(cohorte_id, periodo)`, `find_by_filters()`, `upsert()`
- [ ] 4.5 Crear `repositories/factura_repository.py` con `TenantScopedRepository[Factura]` y métodos básicos (CRUD heredado suficiente)
- [ ] 4.6 Exportar repositorios en `app/repositories/__init__.py`

## 5. Servicios

- [ ] 5.1 Crear `services/salario_service.py` con `SalarioService`:
  - CRUD delegado a repositorios
  - Validación de solapamiento de vigencia antes de crear/actualizar SalarioBase (mismo rol) y SalarioPlus (mismo grupo_id+rol)
  - Verificación de unicidad `(tenant_id, rol, desde)` y `(tenant_id, grupo_id, rol, desde)`

- [ ] 5.2 Crear `services/liquidacion_service.py` con `LiquidacionService`:
  - `calcular(cohorte_id, periodo)`: orquesta el algoritmo de cálculo (ver design.md §Cálculo)
    - Obtener grilla base y plus vigentes para el período
    - Obtener asignaciones activas de la cohorte en el período
    - Por cada usuario activo: determinar grupo_id desde Materia.grupo_materia_id, calcular monto_base, monto_plus (Σ grupo × N comisiones), total
    - Manejar docentes facturantes con `excluido_por_factura = true`
    - Manejar rol NEXO con `es_nexo = true`
    - Upsert de Liquidacion (evitar duplicados por UNIQUE constraint)
  - `cerrar(liquidacion_id)`: cambia estado a Cerrada, valida que no esté ya cerrada, registra auditoría
  - `listar(filtros)`: listado con filtros (cohorte, periodo, usuario, estado)
  - `obtener_kpis(cohorte_id, periodo)`: calcular totales sin factura, con factura, nexo, cantidades
  - `historial(cohorte_id)`: liquidaciones cerradas ordenadas por periodo descendente

- [ ] 5.3 Crear `services/factura_service.py` con `FacturaService`:
  - CRUD con validación de que `usuario.facturador = true` al crear
  - `abonar(factura_id)`: cambia estado a Abonada, registra `abonada_at`
  - Proteger update de facturas ya abonadas (409 Conflict)
  - Sin DELETE (registros financieros inmutables)

- [ ] 5.4 Exportar servicios en `app/services/__init__.py`

## 6. Routers

- [ ] 6.1 Crear `routers/liquidaciones.py` con:
  - `GET /api/liquidaciones/salarios-base` y `GET /api/liquidaciones/salarios-base/{id}` con permiso `liquidaciones:configurar-salarios`
  - `POST /api/liquidaciones/salarios-base` con permiso `liquidaciones:configurar-salarios`
  - `PUT /api/liquidaciones/salarios-base/{id}` con permiso `liquidaciones:configurar-salarios`
  - `DELETE /api/liquidaciones/salarios-base/{id}` con permiso `liquidaciones:configurar-salarios`
  - `GET /api/liquidaciones/salarios-plus` y `GET /api/liquidaciones/salarios-plus/{id}` con permiso `liquidaciones:configurar-salarios`
  - `POST /api/liquidaciones/salarios-plus` con permiso `liquidaciones:configurar-salarios`
  - `PUT /api/liquidaciones/salarios-plus/{id}` con permiso `liquidaciones:configurar-salarios`
  - `DELETE /api/liquidaciones/salarios-plus/{id}` con permiso `liquidaciones:configurar-salarios`
  - `POST /api/liquidaciones/calcular` con permiso `liquidaciones:ver`
  - `GET /api/liquidaciones` con permiso `liquidaciones:ver`
  - `GET /api/liquidaciones/{id}` con permiso `liquidaciones:ver`
  - `POST /api/liquidaciones/{id}/cerrar` con permiso `liquidaciones:cerrar`
  - `GET /api/liquidaciones/kpis` con permiso `liquidaciones:ver`
  - `GET /api/liquidaciones/historial` con permiso `liquidaciones:ver`

- [ ] 6.2 Crear `routers/facturas.py` con:
  - `GET /api/facturas` y `GET /api/facturas/{id}` con permiso `facturas:gestionar`
  - `POST /api/facturas` con permiso `facturas:gestionar`
  - `PUT /api/facturas/{id}` con permiso `facturas:gestionar`
  - `POST /api/facturas/{id}/abonar` con permiso `facturas:gestionar`

- [ ] 6.3 Crear `routers/grupos_materia.py` con CRUD simple para GrupoMateria:
  - `GET /api/admin/grupos-materia` y `GET /api/admin/grupos-materia/{id}` con permiso `liquidaciones:configurar-salarios`
  - `POST /api/admin/grupos-materia` con permiso `liquidaciones:configurar-salarios`
  - `PUT /api/admin/grupos-materia/{id}` con permiso `liquidaciones:configurar-salarios`
  - `DELETE /api/admin/grupos-materia/{id}` con permiso `liquidaciones:configurar-salarios`
- [ ] 6.4 Registrar los 3 routers en `app/api/v1/routers/__init__.py`

## 7. Seed de permisos

- [ ] 7.1 Agregar los 5 permisos nuevos a la seed:
  - `liquidaciones:ver` (modulo: `liquidaciones`, accion: `ver`)
  - `liquidaciones:cerrar` (modulo: `liquidaciones`, accion: `cerrar`)
  - `liquidaciones:configurar-salarios` (modulo: `liquidaciones`, accion: `configurar-salarios`)
  - `liquidaciones:exportar` (modulo: `liquidaciones`, accion: `exportar`)
  - `facturas:gestionar` (modulo: `facturas`, accion: `gestionar`)
- [ ] 7.2 Asignar `liquidaciones:ver` a roles FINANZAS y ADMIN
- [ ] 7.3 Asignar `liquidaciones:cerrar`, `liquidaciones:configurar-salarios`, `liquidaciones:exportar`, `facturas:gestionar` al rol FINANZAS
- [ ] 7.4 Verificar que los endpoints son accesibles con token de FINANZAS

## 8. Tests — GrupoMateria CRUD

- [ ] 8.1 Test: crear GrupoMateria exitosamente → 201
- [ ] 8.2 Test: crear GrupoMateria con clave duplicada en el mismo tenant → 409
- [ ] 8.3 Test: misma clave en distinto tenant → ambos 201 (aislamiento)
- [ ] 8.4 Test: listar GrupoMateria filtra por tenant
- [ ] 8.5 Test: soft delete GrupoMateria → 204

## 9. Tests — Grilla salarial

- [ ] 9.1 Test: crear SalarioBase exitosamente → 201
- [ ] 9.2 Test: crear SalarioBase con rol duplicado y vigencia solapada → 409
- [ ] 9.3 Test: crear SalarioBase con misma combinación en distinto tenant → ambos 201 (aislamiento)
- [ ] 9.4 Test: crear SalarioPlus exitosamente → 201
- [ ] 9.5 Test: crear SalarioPlus con (grupo_id, rol) duplicado y vigencia solapada → 409
- [ ] 9.6 Test: listar SalarioBase filtra por tenant
- [ ] 9.7 Test: listar SalarioPlus filtra por tenant
- [ ] 9.8 Test: soft delete SalarioBase → 204, no aparece en listado
- [ ] 9.9 Test: soft delete SalarioPlus → 204
- [ ] 9.10 Test: actualizar SalarioBase → 200 con datos correctos
- [ ] 9.11 Test: endpoints sin autenticación → 401
- [ ] 9.12 Test: endpoints sin permiso `liquidaciones:configurar-salarios` → 403

## 10. Tests — Cálculo y cierre de liquidaciones

- [ ] 10.1 Test: calcular liquidación exitosamente → 200 con montos correctos (Base + Σ Plus)
- [ ] 10.2 Test: cálculo es idempotente → segunda llamada no crea duplicados
- [ ] 10.3 Test: docente facturante → `excluido_por_factura = true` y excluido del total pagable
- [ ] 10.4 Test: docente sin CBU → excluido del cálculo (RN-26)
- [ ] 10.5 Test: rol NEXO → `es_nexo = true`, suma al total (RN-36)
- [ ] 10.6 Test: grilla con cambios de vigencia → usa el valor correcto según el período (RN-31)
- [ ] 10.7 Test: múltiples comisiones del mismo grupo → acumula N × plus (RN-33/RN-34)
- [ ] 10.8 Test: cerrar liquidación → estado Cerrada, genera audit log con `LIQUIDACION_CERRAR`
- [ ] 10.9 Test: cerrar liquidación ya cerrada → 409 Conflict
- [ ] 10.10 Test: KPIs retornan totales correctos separados por factura/no-factura y nexo
- [ ] 10.11 Test: historial solo retorna liquidaciones Cerradas ordenadas
- [ ] 10.12 Test: liquidaciones aisladas por tenant → no se ven entre tenants

## 11. Tests — Facturas

- [ ] 11.1 Test: crear factura para docente facturante → 201
- [ ] 11.2 Test: crear factura para docente no facturante → 422
- [ ] 11.3 Test: listar facturas filtra por tenant
- [ ] 11.4 Test: abonar factura → estado "Abonada", `abonada_at` seteado
- [ ] 11.5 Test: abonar factura ya abonada → 409
- [ ] 11.6 Test: actualizar factura pendiente → 200
- [ ] 11.7 Test: actualizar factura abonada → 409
- [ ] 11.8 Test: DELETE a factura → 405 (no permitido)
- [ ] 11.9 Test: endpoints sin permiso `facturas:gestionar` → 403

## 12. Limpieza y validación final

- [ ] 13.1 Ejecutar suite completa de tests del módulo → todos verdes
- [ ] 13.2 Verificar cobertura (≥80% líneas, ≥90% reglas de negocio)
- [ ] 13.3 Ejecutar migración desde el head anterior → nueva migración aplicada sin errores
- [ ] 13.4 Verificar rollback → `alembic downgrade` exitoso sin datos huérfanos
