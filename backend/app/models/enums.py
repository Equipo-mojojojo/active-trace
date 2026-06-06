from __future__ import annotations

from enum import StrEnum


class EstadoActivo(StrEnum):
    ACTIVA = "Activa"
    INACTIVA = "Inactiva"


class EstadoComunicacion(StrEnum):
    PENDIENTE = "Pendiente"
    ENVIANDO = "Enviando"
    ENVIADO = "Enviado"
    ERROR = "Error"
    CANCELADO = "Cancelado"
