from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.health import router as health_router
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
    application.include_router(auth_router)
    application.include_router(health_router)
    return application


app = create_app()
