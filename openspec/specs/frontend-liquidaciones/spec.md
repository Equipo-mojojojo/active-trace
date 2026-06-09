## ADDED Requirements

### Requirement: Vista de liquidaciones del período segmentada
El sistema SHALL mostrar en `LiquidacionesPage` (ruta `/finanzas/liquidaciones`) la liquidación del período seleccionado segmentada en 3 tabs: "General" (PROFESOR, TUTOR, COORDINADOR que no facturan), "NEXO", y "Facturas" (docentes facturantes, informativos). Los datos SHALL provenir de una sola llamada a `GET /api/liquidaciones/?periodo={periodo}` que retorna los segmentos `general`, `nexo`, `facturantes`. Cada fila SHALL mostrar: docente, rol (badge de color), comisiones, salario base, plus y total.

#### Scenario: Render de los tres tabs con datos
- **WHEN** un usuario FINANZAS navega a `/finanzas/liquidaciones` con un período seleccionado
- **THEN** ve los tabs "General", "NEXO" y "Facturas", con el tab "General" activo mostrando su tabla de docentes

#### Scenario: Cambio de tab sin re-fetch
- **WHEN** el usuario hace click en el tab "NEXO"
- **THEN** se muestra el segmento NEXO usando los datos ya cargados, sin disparar una nueva request

#### Scenario: Estado vacío sin datos del período
- **WHEN** la respuesta del período no contiene docentes en un segmento
- **THEN** el tab correspondiente muestra un estado vacío informativo en lugar de una tabla en blanco

### Requirement: KPIs de cabecera de liquidación
El sistema SHALL mostrar por encima de los tabs dos KPI cards: "Total sin factura" (`total_sin_factura`) y "Total con factura" (`total_con_factura`), tomados de la respuesta de `GET /api/liquidaciones/`.

#### Scenario: KPIs visibles con montos
- **WHEN** la liquidación del período carga correctamente
- **THEN** se muestran las dos KPI cards con los montos `total_sin_factura` y `total_con_factura` formateados como moneda

#### Scenario: Facturantes excluidos del total sin factura
- **WHEN** existen docentes en el segmento "Facturas"
- **THEN** sus montos aparecen en el segmento informativo y suman al "Total con factura", pero NO al "Total sin factura"

### Requirement: Filtros de liquidación (cohorte, mes, docente)
El sistema SHALL proveer filtros de cohorte, mes y un dropdown opcional de docente por encima de los tabs. Al cambiar un filtro, SHALL re-consultar `GET /api/liquidaciones/` con los parámetros actualizados (`periodo`, `usuario_id`) usando una query key que incluya los filtros.

#### Scenario: Filtrar por período
- **WHEN** el usuario cambia el mes/cohorte del período
- **THEN** la vista re-consulta la liquidación del nuevo período y actualiza tabs y KPIs

#### Scenario: Filtrar por docente específico
- **WHEN** el usuario selecciona un docente en el dropdown
- **THEN** la vista muestra solo la liquidación de ese docente en el período (`usuario_id`)

### Requirement: Cerrar liquidación con confirmación
El sistema SHALL mostrar el botón "Cerrar liquidación" solo a usuarios con permiso `liquidaciones:cerrar`. Al hacer click, SHALL pedir confirmación explícita indicando que la acción es irreversible, y al confirmar SHALL hacer `POST /api/liquidaciones/{periodo}/cerrar`. Tras éxito, SHALL invalidar la query y mostrar la liquidación en modo solo-lectura.

#### Scenario: Confirmación previa al cierre
- **WHEN** el usuario hace click en "Cerrar liquidación"
- **THEN** se muestra un modal de confirmación con el período y la advertencia de irreversibilidad antes de enviar cualquier request

#### Scenario: Cierre exitoso
- **WHEN** el usuario confirma el cierre y el backend responde 200
- **THEN** la vista invalida los datos, recarga y muestra la liquidación como cerrada (solo-lectura), sin el botón de cierre activo

#### Scenario: Intento de cierre de período ya cerrado
- **WHEN** el backend responde 409 al cerrar
- **THEN** la vista muestra un mensaje "La liquidación ya está cerrada" sin romper la pantalla

#### Scenario: Botón de cierre oculto sin permiso
- **WHEN** un usuario FINANZAS sin `liquidaciones:cerrar` ve la página
- **THEN** el botón "Cerrar liquidación" no se renderiza

### Requirement: Exportar liquidación
El sistema SHALL proveer un botón "Exportar" que dispare la descarga de la planilla de liquidación generada por el backend para el período/filtros actuales.

#### Scenario: Disparar exportación
- **WHEN** el usuario hace click en "Exportar"
- **THEN** la app inicia la descarga del archivo de liquidación del período seleccionado

### Requirement: Historial de liquidaciones cerradas
El sistema SHALL proveer `HistorialLiquidacionesPage` (ruta `/finanzas/liquidaciones/historial`) que liste los períodos con liquidaciones cerradas (`GET /api/liquidaciones/historial`) ordenados por período descendente, permitiendo abrir el detalle de un período cerrado.

#### Scenario: Listar períodos cerrados
- **WHEN** el usuario navega a `/finanzas/liquidaciones/historial`
- **THEN** ve la lista de períodos cerrados ordenada de más reciente a más antiguo

#### Scenario: Ver detalle de período cerrado
- **WHEN** el usuario selecciona un período del historial
- **THEN** ve el detalle de esa liquidación cerrada en modo solo-lectura

### Requirement: Protección de acceso a liquidaciones
Todas las rutas `/finanzas/liquidaciones*` SHALL estar protegidas por `AuthGuard` + `PermissionGuard` con permiso `liquidaciones:ver`.

#### Scenario: Acceso sin permiso liquidaciones:ver
- **WHEN** un usuario sin `liquidaciones:ver` navega a `/finanzas/liquidaciones`
- **THEN** la app redirige a `/403`
