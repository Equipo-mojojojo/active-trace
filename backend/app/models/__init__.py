"""ORM models package."""

from app.models.acknowledgment_aviso import AcknowledgmentAviso
from app.models.asignacion import Asignacion
from app.models.audit_log import AuditLog
from app.models.auth_login_attempt import AuthLoginAttempt
from app.models.auth_session import AuthSession
from app.models.aviso import Aviso
from app.models.base import BaseModelMixin, TenantScopedModelMixin
from app.models.calificacion import Calificacion, UmbralMateria
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.comentario_tarea import ComentarioTarea
from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.models.convocado import Convocado
from app.models.enums import (
    AlcanceAviso,
    DiaSemana,
    EstadoActivo,
    EstadoEncuentro,
    EstadoEvaluacion,
    EstadoGuardia,
    EstadoReserva,
    EstadoTarea,
    SeveridadAviso,
    TipoEvaluacion,
)
from app.models.evaluacion import Evaluacion
from app.models.fecha_academica import FechaAcademica
from app.models.guardia import Guardia
from app.models.instancia_encuentro import InstanciaEncuentro
from app.models.materia import Materia
from app.models.programa_materia import ProgramaMateria
from app.models.padron import EntradaPadron, VersionPadron
from app.models.tarea import Tarea
from app.models.password_reset_token import PasswordResetToken
from app.models.permission import Permission
from app.models.refresh_token import RefreshToken
from app.models.reserva_evaluacion import ReservaEvaluacion
from app.models.resultado_evaluacion import ResultadoEvaluacion
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.slot_encuentro import SlotEncuentro
from app.models.tenant import Tenant
from app.models.turno_evaluacion import TurnoEvaluacion
from app.models.user import User
from app.models.usuario import Usuario

__all__ = [
    "AcknowledgmentAviso",
    "AlcanceAviso",
    "Asignacion",
    "AuditLog",
    "AuthLoginAttempt",
    "AuthSession",
    "Aviso",
    "BaseModelMixin",
    "Calificacion",
    "Carrera",
    "Cohorte",
    "ComentarioTarea",
    "Comunicacion",
    "Convocado",
    "DiaSemana",
    "EntradaPadron",
    "EstadoComunicacion",
    "EstadoActivo",
    "EstadoEncuentro",
    "EstadoEvaluacion",
    "EstadoGuardia",
    "EstadoReserva",
    "EstadoTarea",
    "Evaluacion",
    "FechaAcademica",
    "Guardia",
    "InstanciaEncuentro",
    "Materia",
    "PasswordResetToken",
    "ProgramaMateria",
    "Permission",
    "RefreshToken",
    "ReservaEvaluacion",
    "ResultadoEvaluacion",
    "Role",
    "RolePermission",
    "SeveridadAviso",
    "SlotEncuentro",
    "Tarea",
    "Tenant",
    "TenantScopedModelMixin",
    "TipoEvaluacion",
    "TurnoEvaluacion",
    "UmbralMateria",
    "User",
    "Usuario",
    "VersionPadron",
]
