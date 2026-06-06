"""Repositories package."""

from app.repositories.acknowledgment_repository import (
    AcknowledgmentRepository,
)
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.aviso_repository import AvisoRepository
from app.repositories.base import BaseRepository, TenantScopedRepository
from app.repositories.carrera_repository import CarreraRepository
from app.repositories.cohorte_repository import CohorteRepository
from app.repositories.convocado_repository import ConvocadoRepository
from app.repositories.evaluacion_repository import EvaluacionRepository
from app.repositories.materia_repository import MateriaRepository
from app.repositories.reserva_evaluacion_repository import (
    ReservaEvaluacionRepository,
)
from app.repositories.resultado_evaluacion_repository import (
    ResultadoEvaluacionRepository,
)
from app.repositories.turno_evaluacion_repository import (
    TurnoEvaluacionRepository,
)
from app.repositories.user_repository import UserRepository

__all__ = [
    "AcknowledgmentRepository",
    "AuditLogRepository",
    "AuthRepository",
    "AvisoRepository",
    "BaseRepository",
    "CarreraRepository",
    "CohorteRepository",
    "ConvocadoRepository",
    "EvaluacionRepository",
    "MateriaRepository",
    "ReservaEvaluacionRepository",
    "ResultadoEvaluacionRepository",
    "TenantScopedRepository",
    "TurnoEvaluacionRepository",
    "UserRepository",
]
