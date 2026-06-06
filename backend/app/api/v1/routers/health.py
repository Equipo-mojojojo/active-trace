from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    database_status = "up"

    try:
        await db.execute(text("SELECT 1"))
    except (OSError, RuntimeError, SQLAlchemyError):
        database_status = "down"

    return HealthResponse(status="ok", database=database_status)
