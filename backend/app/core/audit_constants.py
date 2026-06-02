"""Audit action code catalog (closed enum).

Provides a single source of truth for all possible ``accion`` values
that can appear in the audit log (RN-24). Every module that writes to
the audit log must use these constants — never raw strings.

Usage::

    from app.core.audit_constants import AuditAction

    await audit_service.register(
        actor_id=user.id,
        tenant_id=user.tenant_id,
        accion=AuditAction.CALIFICACIONES_IMPORTAR,
        materia_id=materia.id,
        filas_afectadas=42,
    )
"""

from __future__ import annotations

from enum import StrEnum


class AuditAction(StrEnum):
    """Catálogo cerrado de códigos de acción para el audit log (RN-24).

    Cada miembro es una constante textual que se almacena en la columna
    ``accion`` de la tabla ``audit_log``. Nunca uses strings literales
    en el código — importá la constante de este enum.

    Para agregar un nuevo código, agregalo aquí. Si el catálogo supera
    ~20 entradas, considerá migrarlo a una tabla en la base de datos.
    """

    # ── Autenticación y sesión ──────────────────────────────────────
    USUARIO_LOGIN = "USUARIO_LOGIN"
    USUARIO_LOGOUT = "USUARIO_LOGOUT"

    # ── Gestión de usuarios ─────────────────────────────────────────
    USUARIO_CREAR = "USUARIO_CREAR"
    USUARIO_MODIFICAR = "USUARIO_MODIFICAR"
    USUARIO_BLOQUEAR = "USUARIO_BLOQUEAR"

    # ── RBAC y permisos ─────────────────────────────────────────────
    ROL_ASIGNAR = "ROL_ASIGNAR"
    ROL_QUITAR = "ROL_QUITAR"
    PERMISO_MODIFICAR = "PERMISO_MODIFICAR"

    # ── Importación de datos ────────────────────────────────────────
    CALIFICACIONES_IMPORTAR = "CALIFICACIONES_IMPORTAR"
    PADRON_CARGAR = "PADRON_CARGAR"

    # ── Comunicaciones ──────────────────────────────────────────────
    COMUNICACION_ENVIAR = "COMUNICACION_ENVIAR"

    # ── Equipos docentes ────────────────────────────────────────────
    ASIGNACION_MODIFICAR = "ASIGNACION_MODIFICAR"

    # ── Liquidaciones ───────────────────────────────────────────────
    LIQUIDACION_CERRAR = "LIQUIDACION_CERRAR"

    # ── Impersonación ───────────────────────────────────────────────
    IMPERSONACION_INICIAR = "IMPERSONACION_INICIAR"
    IMPERSONACION_FINALIZAR = "IMPERSONACION_FINALIZAR"

    # ── Configuración del sistema ───────────────────────────────────
    CONFIGURACION_MODIFICAR = "CONFIGURACION_MODIFICAR"
