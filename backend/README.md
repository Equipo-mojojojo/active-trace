# Backend

## Setup rápido para C-10 / C-11

1. Instalar dependencias del backend en el entorno activo:

   ```bash
   python -m pip install -e .[test]
   ```

2. Verificar dependencias de parseo requeridas por padrón/calificaciones:

   ```bash
   python validate_c10_c11_env.py
   ```

3. Si vas a correr integración/E2E, definir `TEST_DATABASE_URL` apuntando a una base PostgreSQL de prueba.

## Validación dirigida

- Unitarias C-10/C-11:

  ```bash
  pytest tests/test_calificaciones_c10.py tests/test_analisis_c11.py
  ```

- Integración/E2E de C-10/C-11 con base real:

  ```bash
  pytest tests/test_calificaciones_c10.py tests/test_analisis_c11.py
  ```

  Requiere `TEST_DATABASE_URL` configurada; de lo contrario, pytest saltará los casos que dependen de DB.

- C-12 comunicaciones + worker:

  ```bash
  pytest tests/test_comunicacion_c12.py
  ```
