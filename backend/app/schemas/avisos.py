from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, BaseModel

from app.models.enums import AlcanceAviso, SeveridadAviso


class AvisoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    alcance: AlcanceAviso
    materia_id: UUID | None = None
    cohorte_id: UUID | None = None
    rol_destino: str | None = None
    severidad: SeveridadAviso
    titulo: str
    cuerpo: str
    inicio_en: datetime
    fin_en: datetime | None = None
    orden: int = 0
    activo: bool = True
    requiere_ack: bool = False


class AvisoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    alcance: AlcanceAviso | None = None
    materia_id: UUID | None = None
    cohorte_id: UUID | None = None
    rol_destino: str | None = None
    severidad: SeveridadAviso | None = None
    titulo: str | None = None
    cuerpo: str | None = None
    inicio_en: datetime | None = None
    fin_en: datetime | None = None
    orden: int | None = None
    activo: bool | None = None
    requiere_ack: bool | None = None


class AvisoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    alcance: AlcanceAviso
    materia_id: UUID | None = None
    cohorte_id: UUID | None = None
    rol_destino: str | None = None
    severidad: SeveridadAviso
    titulo: str
    cuerpo: str
    inicio_en: datetime
    fin_en: datetime | None = None
    orden: int
    activo: bool
    requiere_ack: bool


class AvisoDetailResponse(AvisoResponse):
    total_acks: int = 0
    total_visibles: int = 0


class AcknowledgmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    aviso_id: UUID
    usuario_id: UUID
    confirmado_at: datetime
