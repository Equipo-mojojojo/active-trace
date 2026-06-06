# audit-admin-api Specification

## Purpose
TBD - created by archiving change c-05-audit-log. Update Purpose after archive.
## Requirements
### Requirement: El sistema SHALL exponer una API REST de consulta del log de auditoría

El sistema SHALL proveer `GET /api/admin/audit-log` protegido con `require_permission("auditoria:ver")` que devuelva registros de auditoría paginados con filtros.

#### Scenario: Consultar log sin filtros
- **WHEN** un usuario con permiso `auditoria:ver` solicita GET /api/admin/audit-log
- **THEN** el sistema SHALL devolver status 200
- **THEN** el sistema SHALL devolver una lista paginada de registros de auditoría del tenant
- **THEN** el sistema SHALL devolver metadatos de paginación (total, page, page_size)

#### Scenario: Consultar log con filtro por rango de fechas
- **WHEN** se solicitan registros con `?desde=2026-01-01&hasta=2026-06-30`
- **THEN** el sistema SHALL devolver solo registros dentro de ese rango

#### Scenario: Consultar log con filtro por actor
- **WHEN** se solicita `?actor_id=<uuid>`
- **THEN** el sistema SHALL devolver solo registros de ese actor

#### Scenario: Consultar log con filtro por código de acción
- **WHEN** se solicita `?accion=CALIFICACIONES_IMPORTAR`
- **THEN** el sistema SHALL devolver solo registros con ese código

#### Scenario: Consultar log con filtro por materia
- **WHEN** se solicita `?materia_id=<uuid>`
- **THEN** el sistema SHALL devolver solo registros de esa materia

#### Scenario: Usuario sin permiso auditoria:ver recibe 403
- **WHEN** un usuario SIN permiso `auditoria:ver` solicita GET /api/admin/audit-log
- **THEN** el sistema SHALL devolver status 403

#### Scenario: Usuario con permiso auditoria:ver:propio solo ve sus acciones
- **WHEN** un usuario con solo `auditoria:ver:propio` solicita GET /api/admin/audit-log
- **THEN** el sistema SHALL devolver solo registros donde actor_id = usuario actual

