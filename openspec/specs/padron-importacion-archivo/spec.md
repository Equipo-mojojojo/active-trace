## ADDED Requirements

### Requirement: Preview de padrón sin persistencia
El sistema SHALL exponer `POST /api/padron/preview` que reciba un archivo `.xlsx` o `.csv`, lo parsee en memoria y retorne los alumnos detectados (nombre, apellidos, email enmascarado, comisión, regional) y las columnas encontradas, sin escribir nada en la base de datos. Requiere permiso `padron:importar`.

#### Scenario: Preview de xlsx retorna alumnos detectados
- **WHEN** el PROFESOR sube un archivo xlsx válido con 10 alumnos
- **THEN** el sistema retorna `200 OK` con `alumnos: [{nombre, apellidos, comision, regional, email_enmascarado}]` y `columnas_detectadas: [...]` sin crear ninguna fila en DB

#### Scenario: Extensión no soportada retorna 422
- **WHEN** el usuario sube un archivo `.pdf` o `.docx`
- **THEN** el sistema retorna `422 Unprocessable Entity` con mensaje de formato no soportado

#### Scenario: Archivo con más de 5000 filas retorna 422
- **WHEN** el archivo tiene más de 5000 filas de datos
- **THEN** el sistema retorna `422` indicando el límite máximo

#### Scenario: Header de columnas insensible a mayúsculas
- **WHEN** el archivo tiene headers `EMAIL`, `Nombre`, `APELLIDOS`
- **THEN** el parser detecta correctamente las columnas independientemente del casing

### Requirement: Importación confirma y persiste nueva versión activa
El sistema SHALL exponer `POST /api/padron/importar` que reciba un archivo `.xlsx`/`.csv` más `materia_id` y `cohorte_id`, parsee el contenido, desactive la versión anterior y cree la nueva versión activa con sus `EntradaPadron`. Requiere permiso `padron:importar`. Registra auditoría `PADRON_CARGAR`.

#### Scenario: Importación exitosa crea nueva versión activa
- **WHEN** el PROFESOR importa un padrón válido para (materia A, cohorte B)
- **THEN** el sistema retorna `201 Created` con el `id` de la nueva `VersionPadron` y el conteo de entradas cargadas

#### Scenario: Importación desactiva versión anterior
- **WHEN** ya existe una versión activa para (materia A, cohorte B) y se importa una nueva
- **THEN** la versión anterior queda `activa=false` y la nueva queda `activa=true`

#### Scenario: Importación genera auditoría PADRON_CARGAR
- **WHEN** se completa una importación exitosa
- **THEN** el sistema registra una entrada en `AuditLog` con `accion=PADRON_CARGAR` y `actor_id` del usuario que importó

#### Scenario: PROFESOR solo puede importar en materias de su asignación
- **WHEN** un PROFESOR intenta importar en una materia para la que no tiene asignación vigente
- **THEN** el sistema retorna `403 Forbidden`

#### Scenario: Email de alumno se almacena cifrado
- **WHEN** se importa un padrón con emails de alumnos
- **THEN** los emails en `entrada_padron` están cifrados en la DB (no texto plano)

### Requirement: Vaciado de padrón scope-isolated por asignación (RN-04)
El sistema SHALL exponer `DELETE /api/padron/vaciar` que elimine (soft delete) la versión activa del padrón para una (materia_id, cohorte_id). Un PROFESOR SHALL poder vaciar solo el padrón de materias en las que tiene asignación vigente. Un COORDINADOR puede vaciar cualquier padrón del tenant. Requiere `padron:importar`.

#### Scenario: PROFESOR vacía su propio padrón
- **WHEN** el PROFESOR llama el endpoint con materia_id de una asignación vigente propia
- **THEN** la versión activa queda con `activa=false` (soft delete, no hard delete) y retorna `200 OK`

#### Scenario: PROFESOR no puede vaciar padrón de otra asignación
- **WHEN** el PROFESOR intenta vaciar una materia para la que no tiene asignación
- **THEN** el sistema retorna `403 Forbidden`

#### Scenario: Vaciar sin versión activa retorna 404
- **WHEN** no existe versión activa para la combinación materia × cohorte solicitada
- **THEN** el sistema retorna `404 Not Found`
