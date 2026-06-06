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
from app.schemas.materia import MateriaCreate, MateriaResponse, MateriaUpdate

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
    "MateriaCreate",
    "MateriaResponse",
    "MateriaUpdate",
]
