## 1. Service y Repository de Equipos

- [x] 1.1 Crear `backend/app/repositories/equipos_repository.py` con métodos: `listar_por_usuario(usuario_id, tenant_id, filtros)`, `listar_por_tenant(tenant_id, filtros)`, `crear_masivo(asignaciones, db)`, `clonar_equipo(origen, destino, nuevas_fechas, db)`, `actualizar_vigencia_equipo(materia_id, carrera_id, cohorte_id, desde, hasta, dry_run, db)` — todos con scope de tenant por defecto
- [x] 1.2 Agregar derivación de `estado_vigencia` en las queries del repositorio con expresión `CASE WHEN hasta IS NULL OR hasta >= today THEN 'Vigente' ELSE 'Vencida' END`
- [x] 1.3 Crear `backend/app/services/equipos_service.py` con métodos de dominio: `mis_equipos(actor, filtros)`, `consultar_asignaciones(actor, filtros)`, `asignacion_masiva(actor, payload)`, `clonar_equipo(actor, payload)`, `modificar_vigencia(actor, payload)`, `exportar_csv(actor, filtros)`
- [x] 1.4 Implementar lógica de clonado en `EquiposService.clonar_equipo`: obtener asignaciones vigentes del origen → duplicar con nueva `cohorte_id` y fechas → manejar `hasta=NULL` → registrar auditoría por cada asignación
- [x] 1.5 Implementar lógica de asignación masiva en `EquiposService.asignacion_masiva`: validar unicidad de cada elemento → crear en transacción única → revertir en 409 si hay conflicto → registrar auditoría

## 2. Tests — Service y Repository (TDD: test primero)

- [x] 2.1 Test: `listar_por_usuario` retorna solo asignaciones del usuario autenticado dentro del tenant (aislamiento multi-tenant)
- [x] 2.2 Test: `estado_vigencia` derivado correcto — Vigente con `hasta IS NULL`, Vigente con `hasta >= hoy`, Vencida con `hasta < hoy`
- [x] 2.3 Test: `clonar_equipo` duplica asignaciones vigentes del origen con nueva cohorte y fechas; no modifica el origen
- [x] 2.4 Test: `clonar_equipo` — asignación con `hasta=NULL` recibe la `hasta` del período destino
- [x] 2.5 Test: `clonar_equipo` — equipo sin asignaciones vigentes retorna `clonadas=0` sin error
- [x] 2.6 Test: `asignacion_masiva` — 5 usuarios asignados en transacción única → 5 asignaciones creadas
- [x] 2.7 Test: `asignacion_masiva` — conflicto en un usuario revierte toda la transacción (ninguna asignación queda creada)
- [x] 2.8 Test: `modificar_vigencia` con `dry_run=True` retorna conteo sin modificar datos
- [x] 2.9 Test: `modificar_vigencia` sin `dry_run` actualiza `desde`/`hasta` de todas las asignaciones del equipo

## 3. Schemas Pydantic (request/response)

- [x] 3.1 Crear `backend/app/schemas/equipos.py` con `model_config = ConfigDict(extra='forbid')` en todos los schemas
- [x] 3.2 Schema request `MisEquiposFiltros`: campos opcionales `estado`, `materia_id`, `rol`, `carrera_id`, `cohorte_id`
- [x] 3.3 Schema response `AsignacionResponse`: incluye `estado_vigencia` derivado, datos del usuario (nombre, sin PII cifrada expuesta), materia, carrera, cohorte
- [x] 3.4 Schema request `AsignacionMasivaRequest`: `usuarios: list[UUID]`, `rol`, `materia_id`, `carrera_id`, `cohorte_id`, `comisiones`, `responsable_id`, `desde`, `hasta`
- [x] 3.5 Schema request `ClonarEquipoRequest`: `materia_id`, `carrera_id`, `cohorte_id_origen`, `cohorte_id_destino`, `desde`, `hasta`
- [x] 3.6 Schema request `ModificarVigenciaRequest`: `materia_id`, `carrera_id`, `cohorte_id`, `desde`, `hasta`, `dry_run: bool = False`

## 4. Router de Equipos

- [x] 4.1 Crear `backend/app/routers/equipos.py` con APIRouter prefix `/api/equipos`
- [x] 4.2 `GET /mis-equipos` — sin guard de permiso extra; identidad del actor desde JWT; llama `EquiposService.mis_equipos`
- [x] 4.3 `GET /asignaciones` — guard `require_permission("equipos:asignar")`; llama `EquiposService.consultar_asignaciones`
- [x] 4.4 `POST /asignaciones/masiva` — guard `require_permission("equipos:asignar")`; llama `EquiposService.asignacion_masiva`; retorna 201 o 409
- [x] 4.5 `POST /clonar` — guard `require_permission("equipos:asignar")`; llama `EquiposService.clonar_equipo`
- [x] 4.6 `PATCH /vigencia` — guard `require_permission("equipos:asignar")`; llama `EquiposService.modificar_vigencia`; soporta `dry_run`
- [x] 4.7 `GET /export` — guard `require_permission("equipos:asignar")`; llama `EquiposService.exportar_csv`; retorna `StreamingResponse` con `Content-Type: text/csv` y `Content-Disposition: attachment`
- [x] 4.8 Registrar el router en `backend/app/main.py`

## 5. Tests — Router/API (TDD: test primero)

- [x] 5.1 Test: `GET /api/equipos/mis-equipos` con JWT válido → 200 con asignaciones del actor
- [x] 5.2 Test: `GET /api/equipos/mis-equipos` con filtro `estado=Vigente` → solo retorna Vigentes
- [x] 5.3 Test: aislamiento multi-tenant — docente del tenant A no ve asignaciones del tenant B
- [x] 5.4 Test: `GET /api/equipos/asignaciones` sin permiso `equipos:asignar` → 403
- [x] 5.5 Test: `POST /api/equipos/asignaciones/masiva` → 201 con 3 asignaciones creadas
- [x] 5.6 Test: `POST /api/equipos/asignaciones/masiva` con conflicto → 409, ninguna asignación creada
- [x] 5.7 Test: `POST /api/equipos/clonar` → asignaciones clonadas con nueva cohorte y fechas correctas
- [x] 5.8 Test: `PATCH /api/equipos/vigencia` con `dry_run=true` → 200, datos sin modificar
- [x] 5.9 Test: `PATCH /api/equipos/vigencia` sin dry_run → vigencias actualizadas en DB
- [x] 5.10 Test: `GET /api/equipos/export` → 200, `Content-Type: text/csv`, body con filas de asignaciones

## 6. Auditoría

- [x] 6.1 Verificar que `AuditAction.ASIGNACION_MODIFICAR` existe en el catálogo de C-05 (agregar si falta)
- [x] 6.2 Test: `asignacion_masiva` de 3 usuarios genera 3 entradas `ASIGNACION_MODIFICAR` en `AuditLog` con `actor_id` del coordinador
- [x] 6.3 Test: `clonar_equipo` de 2 asignaciones genera 2 entradas de auditoría
- [x] 6.4 Test: `modificar_vigencia` genera una entrada de auditoría por asignación afectada
