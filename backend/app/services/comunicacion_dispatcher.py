from __future__ import annotations

from dataclasses import dataclass

from app.models.comunicacion import Comunicacion


class ComunicacionDispatchError(RuntimeError):
    pass


@dataclass(slots=True)
class DispatchResult:
    external_id: str | None = None


class ComunicacionDispatcher:
    async def send(self, comunicacion: Comunicacion) -> DispatchResult:
        return DispatchResult(external_id=f"trace-{comunicacion.id}")
