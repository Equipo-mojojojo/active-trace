"""Repositories package."""

from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.base import BaseRepository, TenantScopedRepository
from app.repositories.carrera_repository import CarreraRepository
from app.repositories.cohorte_repository import CohorteRepository
from app.repositories.materia_repository import MateriaRepository
from app.repositories.user_repository import UserRepository

__all__ = [
    "AuditLogRepository",
    "AuthRepository",
    "BaseRepository",
    "CarreraRepository",
    "CohorteRepository",
    "MateriaRepository",
    "TenantScopedRepository",
    "UserRepository",
]
