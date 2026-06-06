from __future__ import annotations

import asyncio
import logging

from app.core.config import get_settings
from app.core.database import get_session_factory, initialize_database
from app.core.logging import configure_logging
from app.workers.comunicacion_worker import process_pending_communications


async def run_worker() -> None:
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL)
    initialize_database(settings)
    logger = logging.getLogger(__name__)
    logger.info("Worker de comunicaciones iniciado")
    session_factory = get_session_factory()

    while True:
        async with session_factory() as session:
            try:
                processed = await process_pending_communications(session)
                await session.commit()
                logger.info(
                    "Worker iteración completada", extra={"processed": processed}
                )
            except Exception:
                await session.rollback()
                logger.exception("Worker de comunicaciones falló en una iteración")
        await asyncio.sleep(1)


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
