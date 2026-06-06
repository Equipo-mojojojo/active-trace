from __future__ import annotations

import asyncio
import logging

from app.core.config import get_settings
from app.core.database import initialize_database
from app.core.logging import configure_logging


async def run_worker() -> None:
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL)
    initialize_database(settings)

    from app.workers.comunicacion_worker import ComunicacionWorker

    worker = ComunicacionWorker()
    await worker.run()


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
