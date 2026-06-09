"""
Elimina todos los usuarios de dev y los recrea con el SECRET_KEY correcto.

Usar cuando el SECRET_KEY cambió y los email_lookup quedaron desincronizados.

Usage:
    python -m scripts.reset_users
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.auth_session import AuthSession
from app.models.base import BaseModelMixin  # noqa: F401
from app.models.refresh_token import RefreshToken
from app.models.user import User


async def main() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        r = await session.execute(delete(RefreshToken))
        print(f"[ok] {r.rowcount} refresh_token(s) eliminado(s)")
        s = await session.execute(delete(AuthSession))
        print(f"[ok] {s.rowcount} sesion(es) eliminada(s)")
        u = await session.execute(delete(User))
        await session.commit()
        print(f"[ok] {u.rowcount} usuario(s) eliminado(s)")

    await engine.dispose()
    print("Ahora corré: python -m scripts.seed_dev")


if __name__ == "__main__":
    asyncio.run(main())
