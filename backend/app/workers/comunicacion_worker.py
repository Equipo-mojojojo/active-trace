"""ComunicacionWorker — C-12.

Async polling worker that dispatches outgoing communications from the
`comunicacion` queue table.

Lifecycle:
  1. On startup: recover orphan messages stuck in ENVIANDO state.
  2. Main loop: poll for PENDIENTE messages, transition states, attempt send.
  3. Retry logic: up to WORKER_MAX_RETRIES attempts with exponential backoff.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import timedelta
from typing import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comunicacion import Comunicacion
from app.models.enums import EstadoComunicacion

logger = logging.getLogger(__name__)

_ORPHAN_TIMEOUT_MINUTES = 5
_POLL_INTERVAL_SECONDS = 10
_BATCH_SIZE = 50


class ComunicacionWorker:
    def __init__(self) -> None:
        self._max_retries = int(os.getenv("WORKER_MAX_RETRIES", "3"))

    # ── Send stub (dry-run until real email provider is wired) ───────

    async def _send(self, comunicacion: Comunicacion) -> None:
        logger.info(
            "[DRY_RUN] Enviando comunicacion id=%s lote=%s",
            comunicacion.id,
            comunicacion.lote_id,
        )

    # ── Retry logic ──────────────────────────────────────────────────

    async def _attempt_send(
        self,
        comunicacion: Comunicacion,
        send_fn: Callable[[Comunicacion], Awaitable[None]] | None = None,
        *,
        base_delay: float = 1.0,
    ) -> None:
        send = send_fn or self._send
        last_exc: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                await send(comunicacion)
                comunicacion.marcar_enviado()
                return
            except Exception as exc:
                last_exc = exc
                comunicacion.reintento_count += 1
                logger.warning(
                    "Comunicacion id=%s attempt=%d/%d failed: %s",
                    comunicacion.id,
                    attempt + 1,
                    self._max_retries,
                    exc,
                )
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(base_delay * (2**attempt))

        comunicacion.marcar_error()
        if last_exc:
            comunicacion.detalle = str(last_exc)[:500]

    # ── Orphan recovery ──────────────────────────────────────────────

    async def _recover_orphans(self, session: AsyncSession) -> None:
        from app.repositories.comunicacion_repository import ComunicacionRepository

        repo = ComunicacionRepository(
            session, "00000000-0000-0000-0000-000000000000"
        )
        timeout = timedelta(minutes=_ORPHAN_TIMEOUT_MINUTES)
        orphans = await repo.listar_huerfanos_global(timeout)

        if orphans:
            logger.warning("Recovering %d orphaned ENVIANDO messages", len(orphans))

        for orphan in orphans:
            orphan.detalle = "worker_restart_recovery"
            orphan.marcar_error()

        if orphans:
            await session.commit()

    # ── Main loop ────────────────────────────────────────────────────

    async def _process_batch(self, session: AsyncSession) -> int:
        from app.models.tenant import Tenant
        from app.repositories.comunicacion_repository import ComunicacionRepository
        from sqlalchemy import select

        tenants_result = await session.execute(
            select(Tenant).where(Tenant.deleted_at.is_(None))
        )
        tenants = list(tenants_result.scalars().all())

        processed = 0
        for tenant in tenants:
            repo = ComunicacionRepository(session, tenant.id)
            mensajes = await repo.listar_por_estado_pendiente(
                requiere_aprobacion=tenant.requiere_aprobacion_comunicaciones,
                limit=_BATCH_SIZE,
            )
            for m in mensajes:
                m.marcar_enviando()
                await session.flush()
                await self._attempt_send(m)
                await session.commit()
                processed += 1

        return processed

    async def run(self) -> None:
        from app.core.database import get_session_factory

        factory = get_session_factory()
        logger.info("ComunicacionWorker iniciado (max_retries=%d)", self._max_retries)

        async with factory() as session:
            await self._recover_orphans(session)

        while True:
            try:
                async with factory() as session:
                    count = await self._process_batch(session)
                    if count:
                        logger.info("Batch processed: %d messages", count)
            except Exception as exc:
                logger.error("Worker batch error: %s", exc, exc_info=True)

            await asyncio.sleep(_POLL_INTERVAL_SECONDS)
