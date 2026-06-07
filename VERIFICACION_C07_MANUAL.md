# C-07 Usuarios y Asignaciones — Verificación Manual

## Status
- ✅ Migration executed (0006_create_usuario_asignacion)
- ✅ Test suite running (21 passed, 1 minor warning, 127 skipped)
- 📋 Manual verification NEXT

## Verificaciones a Hacer

### 1. Levantar el servidor FastAPI
```bash
cd backend
python -m uvicorn app.main:app --reload
```

Debería ver:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 2. Health Check
```bash
curl -i http://127.0.0.1:8000/health
```

Esperado:
```
HTTP/1.1 200 OK
{"status":"ok","database":"up"}
```

### 3. Crear un tenant (si no existe)
```bash
# Primero necesitamos un token de admin. Si tenés en test_data:
# Usar el token de test o generar uno manualmente
curl -X POST http://127.0.0.1:8000/api/tenants \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Test Tenant","slug":"test-tenant"}'
```

### 4. Crear un Usuario (PII será cifrada)
```bash
# Asumir tenant_id = "test-tenant-uuid"
# Necesita permiso "usuarios:crear"

curl -X POST http://127.0.0.1:8000/api/admin/usuarios \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "John",
    "apellidos": "Doe",
    "email": "john@example.com",
    "dni": "12345678",
    "cuil": "20-12345678-9",
    "cbu": "1234567890123456789023",
    "alias_cbu": "PEPE.LOPEZ.CUENTA",
    "legajo": "LGJ001"
  }'
```

Verificar:
- Response NO expone `dni`, `cbu`, `cuil`, `alias_cbu` (solo id, nombre, apellidos, email_masked)
- Status 201 Created

### 5. Listar Usuarios
```bash
curl -i http://127.0.0.1:8000/api/admin/usuarios \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

Verificar:
- PII not in response (DTOs omit sensitive fields)
- Status 200
- Multiple users visible but only from same tenant

### 6. Crear una Asignación (Usuario → Rol)
```bash
# Asumir usuario_id del paso anterior
# Asignar rol PROFESOR a una materia

curl -X POST http://127.0.0.1:8000/api/asignaciones \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "usuario_id": "<usuario_uuid>",
    "rol": "PROFESOR",
    "materia_id": "<materia_uuid>",
    "desde": "2026-01-01",
    "hasta": "2026-06-30",
    "responsable_id": null
  }'
```

Verificar:
- Status 201 Created
- Response includes `estado_vigencia: "vigente"` (since today is within desde/hasta)

### 7. Verificar Vigencia Computada
```bash
# Crear otra asignación vencida (in the past)
curl -X POST http://127.0.0.1:8000/api/asignaciones \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "usuario_id": "<usuario_uuid>",
    "rol": "TUTOR",
    "carrera_id": "<carrera_uuid>",
    "desde": "2025-01-01",
    "hasta": "2025-12-31",
    "responsable_id": null
  }'
```

GET the assignment:
```bash
curl http://127.0.0.1:8000/api/asignaciones/<asignacion_id> \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

Verificar:
- `estado_vigencia: "vencida"` (since until date is in the past)
- Vencida assignment is kept (not deleted) but won't grant permissions

### 8. Multi-Tenancy Isolation
```bash
# Create another tenant's token
# Try to GET /api/admin/usuarios with that token

# Should NOT see users from other tenants
# If you try, should get 403 or empty list
```

### 9. PII Not in Logs
```bash
# Check backend console/logs
# Grep for "john@example.com" or "12345678" (DNI)
# Should NOT appear in plaintext

# Email/DNI should only appear as encrypted blobs or hashes
```

### 10. Coverage Report
```bash
cd backend
python -m pytest tests/ --cov=app --cov-report=term-missing
```

Esperado:
- ≥80% line coverage
- ≥90% business rules (vigency, encryption, multi-tenancy)

## Si Todo Anda ✅

Archive C-07:
```bash
openspec archive --change "usuarios-y-asignaciones"
```

Esto:
- Mueve los specs a `openspec/specs/`
- Marca C-07 como completado en CHANGES.md
- Desbloquea: C-08, C-09, C-21, etc.

## Troubleshooting

| Error | Solución |
|-------|----------|
| `Connection refused 127.0.0.1:5432` | `docker-compose ps postgres` — asegurar que está UP |
| `usuario_id invalid` | Verificar que el UUID del usuario existe (GET /api/admin/usuarios) |
| `Permission denied (usuarios:crear)` | Verificar que el JWT token tiene la permission correcta |
| `PII exposed in response` | Bug en DTOs — revisar que `UsuarioResponseDTO` omite email/dni/cbu |
| `Tests still skipped` | Tests pueden requerir fixtures — ejecutar solo uno: `pytest tests/test_usuario_asignacion_c07.py::test_usuario_pii_not_in_response_dto -xvs` |
