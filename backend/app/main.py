from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.routers.analisis import router as analisis_router
from app.api.v1.routers.facturas import router as facturas_router
from app.api.v1.routers.liquidaciones import router as liquidaciones_router
from app.api.v1.routers.metricas_auditoria import router as metricas_auditoria_router
from app.api.v1.routers.perfil import router as perfil_router
from app.api.v1.routers.inbox import router as inbox_router
from app.api.v1.routers.asignaciones import router as asignaciones_router
from app.api.v1.routers.avisos import router as avisos_router
from app.api.v1.routers.calificaciones import router as calificaciones_router
from app.api.v1.routers.coloquios import router as coloquios_router
from app.api.v1.routers.comunicaciones import router as comunicaciones_router
from app.api.v1.routers.encuentros import router as encuentros_router
from app.api.v1.routers.equipos import router as equipos_router
from app.api.v1.routers.audit import router as audit_router
from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.carreras import router as carreras_router
from app.api.v1.routers.cohortes import router as cohortes_router
from app.api.v1.routers.fechas_academicas import router as fechas_academicas_router
from app.api.v1.routers.guardias import router as guardias_router
from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.impersonacion import router as impersonacion_router
from app.api.v1.routers.materias import router as materias_router
from app.api.v1.routers.programas import router as programas_router
from app.api.v1.routers.padron import router as padron_router
from app.api.v1.routers.roles import router as roles_router
from app.api.v1.routers.tareas import router as tareas_router
from app.api.v1.routers.usuarios import router as usuarios_router
from app.core.audit_middleware import AuditMiddleware
from app.core.config import get_settings
from app.core.database import dispose_engine, initialize_database
from app.core.logging import configure_logging
from app.core.observability import instrument_app, uninstrument_app


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL)
    initialize_database(settings)
    instrument_app(application, settings)

    try:
        yield
    finally:
        uninstrument_app(application)
        await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL)

    application = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        lifespan=lifespan,
    )
    application.add_middleware(AuditMiddleware)
    application.include_router(analisis_router)
    application.include_router(asignaciones_router)
    application.include_router(avisos_router)
    application.include_router(calificaciones_router)
    application.include_router(coloquios_router)
    application.include_router(comunicaciones_router)
    application.include_router(encuentros_router)
    application.include_router(equipos_router)
    application.include_router(fechas_academicas_router)
    application.include_router(guardias_router)
    application.include_router(audit_router)
    application.include_router(auth_router)
    application.include_router(carreras_router)
    application.include_router(cohortes_router)
    application.include_router(health_router)
    application.include_router(impersonacion_router)
    application.include_router(materias_router)
    application.include_router(padron_router)
    application.include_router(programas_router)
    application.include_router(roles_router)
    application.include_router(tareas_router)
    application.include_router(usuarios_router)
    application.include_router(liquidaciones_router)
    application.include_router(facturas_router)
    application.include_router(metricas_auditoria_router)
    application.include_router(perfil_router)
    application.include_router(inbox_router)
    return application


app = create_app()
