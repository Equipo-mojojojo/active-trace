## ADDED Requirements

### Requirement: Una sola versión activa de padrón por materia × cohorte
El sistema SHALL garantizar que en todo momento exista como máximo una `VersionPadron` con `activa=true` para cada combinación `(tenant_id, materia_id, cohorte_id)`. Al activar una nueva versión, el sistema SHALL desactivar la anterior en la misma transacción, sin borrarla.

#### Scenario: Activar nueva versión desactiva la anterior
- **WHEN** se importa un nuevo padrón para (materia X, cohorte Y) cuando ya existe una versión activa
- **THEN** la versión anterior queda con `activa=false` y la nueva queda con `activa=true`, ambas persistidas

#### Scenario: Primera carga no tiene versión previa que desactivar
- **WHEN** se importa un padrón para una combinación (materia, cohorte) que nunca tuvo padrón
- **THEN** el sistema crea la primera versión con `activa=true` sin errores

#### Scenario: Aislamiento multi-tenant en versiones
- **WHEN** el tenant A activa una nueva versión de padrón
- **THEN** las versiones del tenant B no son afectadas

### Requirement: EntradaPadron puede existir sin cuenta de usuario
El sistema SHALL permitir registrar una `EntradaPadron` con `usuario_id=NULL` cuando el alumno aún no tiene cuenta de usuario en el sistema. El campo `email` SHALL almacenarse cifrado (AES-256).

#### Scenario: Entrada sin usuario_id se persiste correctamente
- **WHEN** se importa un padrón con un alumno cuyo email no corresponde a ningún Usuario registrado
- **THEN** la EntradaPadron se crea con `usuario_id=NULL` y el email cifrado en reposo

#### Scenario: Email cifrado no aparece en texto plano en respuestas de listado
- **WHEN** se consulta el historial de versiones de un padrón
- **THEN** el campo `email` de las entradas NO aparece en texto plano en el response

### Requirement: Historial de versiones accesible por COORDINADOR y ADMIN
El sistema SHALL exponer `GET /api/padron/versiones` que retorne el listado de versiones (activa y anteriores) para una combinación (materia_id, cohorte_id) dentro del tenant. Requiere permiso `padron:importar`.

#### Scenario: Historial incluye versión activa e inactivas
- **WHEN** el COORDINADOR consulta versiones de una materia con 3 importaciones históricas
- **THEN** el sistema retorna 3 entradas con `activa=true` para la más reciente y `activa=false` para las anteriores

#### Scenario: Consulta sin versiones previas retorna lista vacía
- **WHEN** la combinación materia × cohorte nunca tuvo padrón importado
- **THEN** el sistema retorna `200 OK` con `data: []`
