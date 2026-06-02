## ADDED Requirements

### Requirement: Cifrado AES-256 de atributos sensibles en reposo

El sistema SHALL proveer una utilidad de infraestructura para cifrar y descifrar atributos sensibles usando AES-256 y la clave configurada en `ENCRYPTION_KEY`, de modo que los datos protegidos nunca se almacenen en texto plano.

#### Scenario: Cifrado antes de persistir
- **WHEN** una capa de persistencia almacena un atributo marcado como sensible
- **THEN** el valor persistido queda cifrado usando la utilidad estándar de la plataforma
- **AND** no coincide con el texto plano original

#### Scenario: Descifrado para uso interno controlado
- **WHEN** una capa autorizada necesita recuperar el valor original de un atributo cifrado
- **THEN** la utilidad devuelve el texto plano correcto a partir del valor persistido

### Requirement: Round-trip verificable de cifrado

El sistema SHALL validar mediante tests que un valor cifrado puede descifrarse correctamente con la misma clave y que el proceso es determinista respecto de su integridad funcional.

#### Scenario: Valor sensible conserva su contenido tras encrypt/decrypt
- **WHEN** un valor sensible se cifra y luego se descifra con la misma clave configurada
- **THEN** el resultado final coincide exactamente con el valor original

### Requirement: Datos sensibles no se exponen en logs

El sistema SHALL evitar que la utilidad de cifrado, los repositories o los tests expongan en logs operativos el valor en texto plano de atributos sensibles.

#### Scenario: Operación sensible no registra PII en claro
- **WHEN** se ejecuta una operación que cifra o descifra un atributo sensible
- **THEN** los logs técnicos no contienen el valor en texto plano procesado
