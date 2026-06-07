## ADDED Requirements

### Requirement: El sistema SHALL capturar IP y user_agent de cada request

El sistema SHALL implementar un middleware FastAPI que, para cada request entrante, extraiga la dirección IP del cliente y el User-Agent, y los exponga a través de `request.state` para que AuditService pueda usarlos.

#### Scenario: Capturar IP de X-Forwarded-For
- **WHEN** el request incluye el header `X-Forwarded-For: 203.0.113.42`
- **THEN** request.state.ip SHALL ser `203.0.113.42`

#### Scenario: Capturar IP de remote_addr cuando no hay X-Forwarded-For
- **WHEN** el request NO incluye el header `X-Forwarded-For`
- **THEN** request.state.ip SHALL ser `request.client.host`

#### Scenario: Capturar User-Agent
- **WHEN** el request incluye el header `User-Agent: Mozilla/5.0 ...`
- **THEN** request.state.user_agent SHALL ser el valor del header

#### Scenario: Request sin User-Agent
- **WHEN** el request NO incluye el header `User-Agent`
- **THEN** request.state.user_agent SHALL ser `None`
