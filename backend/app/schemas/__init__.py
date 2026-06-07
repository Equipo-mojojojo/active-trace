"""Pydantic schemas package."""

from app.schemas.avisos import (
    AcknowledgmentResponse,
    AvisoCreate,
    AvisoDetailResponse,
    AvisoResponse,
    AvisoUpdate,
)
from app.schemas.carrera import CarreraCreate, CarreraResponse, CarreraUpdate
from app.schemas.cohorte import CohorteCreate, CohorteResponse, CohorteUpdate
from app.schemas.fecha_academica import (
    FechaAcademicaCreate,
    FechaAcademicaResponse,
    FechaAcademicaUpdate,
)
from app.schemas.materia import MateriaCreate, MateriaResponse, MateriaUpdate
from app.schemas.programa_materia import (
    ProgramaMateriaCreate,
    ProgramaMateriaResponse,
    ProgramaMateriaUpdate,
)

__all__ = [
    "AcknowledgmentResponse",
    "AvisoCreate",
    "AvisoDetailResponse",
    "AvisoResponse",
    "AvisoUpdate",
    "CarreraCreate",
    "CarreraResponse",
    "CarreraUpdate",
    "CohorteCreate",
    "CohorteResponse",
    "CohorteUpdate",
    "FechaAcademicaCreate",
    "FechaAcademicaResponse",
    "FechaAcademicaUpdate",
    "MateriaCreate",
    "MateriaResponse",
    "MateriaUpdate",
    "ProgramaMateriaCreate",
    "ProgramaMateriaResponse",
    "ProgramaMateriaUpdate",
]
