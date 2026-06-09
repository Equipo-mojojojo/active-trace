## ADDED Requirements

### Requirement: Tabla de Salario Base por rol con inline edit
El sistema SHALL mostrar en `GrillaSalarialPage` (ruta `/finanzas/grilla-salarial`) una card "Salario base por rol" con una tabla de `SalarioBase` (`GET /api/liquidaciones/salarios/base`). Cada fila SHALL mostrar: rol (badge), monto, vigencia desde, vigencia hasta y acciones inline editar/eliminar. Un botón "Nueva fila" SHALL agregar una fila editable. Crear usa `POST` y editar usa `PUT /api/liquidaciones/salarios/base/{id}`.

#### Scenario: Listar salarios base
- **WHEN** un usuario con `liquidaciones:configurar-salarios` navega a `/finanzas/grilla-salarial`
- **THEN** ve la tabla de salario base por rol con sus vigencias

#### Scenario: Crear salario base con "Nueva fila"
- **WHEN** el usuario hace click en "Nueva fila", completa rol, monto y vigencia desde, y guarda
- **THEN** se hace POST y, tras éxito, la fila se persiste y la tabla se invalida y refresca

#### Scenario: Editar salario base inline
- **WHEN** el usuario hace click en editar en una fila, modifica el monto y guarda
- **THEN** se hace PUT y la fila refleja el valor actualizado

#### Scenario: Error de vigencia solapada al guardar
- **WHEN** el backend responde 409 por solapamiento de vigencia
- **THEN** la fila en edición muestra el error inline y conserva los datos ingresados sin descartarlos

### Requirement: Tabla de Salario Plus por grupo × rol con inline edit
El sistema SHALL mostrar una card "Plus por grupo" con una tabla de `SalarioPlus` (`GET /api/liquidaciones/salarios/plus`). Cada fila SHALL mostrar: clave/grupo, rol (badge), descripción, monto, vigencia desde, vigencia hasta y acciones inline. Crear usa `POST` y editar usa `PUT /api/liquidaciones/salarios/plus/{id}`.

#### Scenario: Listar plus
- **WHEN** el usuario abre la grilla salarial
- **THEN** ve la tabla de plus con clave de grupo, rol, descripción, monto y vigencias

#### Scenario: Crear plus inline
- **WHEN** el usuario agrega una fila con grupo, rol, monto, descripción y vigencia desde, y guarda
- **THEN** se hace POST y la fila se persiste tras éxito

#### Scenario: Filtrar plus por grupo o rol
- **WHEN** el usuario filtra por grupo y/o rol
- **THEN** la tabla muestra solo los registros que coinciden

### Requirement: Date-range de vigencia en modo edición
Las filas en modo edición SHALL ofrecer un control de rango de vigencia (desde / hasta), permitiendo `hasta` vacío (vigencia abierta).

#### Scenario: Vigencia abierta sin fecha hasta
- **WHEN** el usuario deja "vigencia hasta" vacío y guarda
- **THEN** el registro se persiste con `hasta` nulo (vigencia abierta)

### Requirement: Protección de acceso a la grilla salarial
La ruta `/finanzas/grilla-salarial` SHALL estar protegida por `AuthGuard` + `PermissionGuard` con permiso `liquidaciones:configurar-salarios`.

#### Scenario: Acceso sin permiso
- **WHEN** un usuario sin `liquidaciones:configurar-salarios` navega a `/finanzas/grilla-salarial`
- **THEN** la app redirige a `/403`
