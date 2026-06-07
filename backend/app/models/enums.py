from __future__ import annotations

from enum import StrEnum


class EstadoActivo(StrEnum):
    ACTIVA = "Activa"
    INACTIVA = "Inactiva"


class EstadoEncuentro(StrEnum):
    PROGRAMADO = "Programado"
    REALIZADO = "Realizado"
    CANCELADO = "Cancelado"


class DiaSemana(StrEnum):
    LUNES = "Lunes"
    MARTES = "Martes"
    MIERCOLES = "Miércoles"
    JUEVES = "Jueves"
    VIERNES = "Viernes"
    SABADO = "Sábado"
    DOMINGO = "Domingo"


class EstadoGuardia(StrEnum):
    PENDIENTE = "Pendiente"
    REALIZADA = "Realizada"
    CANCELADA = "Cancelada"


class TipoEvaluacion(StrEnum):
    PARCIAL = "Parcial"
    TP = "TP"
    COLOQUIO = "Coloquio"
    RECUPERATORIO = "Recuperatorio"


class EstadoEvaluacion(StrEnum):
    ABIERTA = "Abierta"
    CERRADA = "Cerrada"


class EstadoReserva(StrEnum):
    ACTIVA = "Activa"
    CANCELADA = "Cancelada"


class AlcanceAviso(StrEnum):
    GLOBAL = "Global"
    POR_MATERIA = "PorMateria"
    POR_COHORTE = "PorCohorte"
    POR_ROL = "PorRol"


class SeveridadAviso(StrEnum):
    INFO = "Info"
    ADVERTENCIA = "Advertencia"
    CRITICO = "Crítico"


class EstadoTarea(StrEnum):
    PENDIENTE = "Pendiente"
    EN_PROGRESO = "En progreso"
    RESUELTA = "Resuelta"
    CANCELADA = "Cancelada"
