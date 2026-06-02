from __future__ import annotations

import asyncio
import logging

from app.core.config import get_settings
from app.core.logging import configure_logging


async def run_worker() -> None:
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL)
    logging.getLogger(__name__).info("Worker placeholder iniciado")
    await asyncio.Event().wait()


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
