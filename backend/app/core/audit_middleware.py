"""Audit middleware — captures per-request context.

Extracts the client IP address and User-Agent header from every
incoming request and stores them in ``request.state`` so that
``AuditService`` (and any other component) can read them without
needing to parse headers again.
"""

from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware that injects ``ip`` and ``user_agent`` into ``request.state``.

    IP resolution strategy (matching standard reverse-proxy conventions):
        1. ``X-Forwarded-For`` header (first address if multiple)
        2. ``X-Real-IP`` header
        3. ``request.client.host`` (direct connection)
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        ip = self._resolve_client_ip(request)
        user_agent = request.headers.get("User-Agent")

        request.state.ip = ip
        request.state.user_agent = user_agent

        return await call_next(request)

    @staticmethod
    def _resolve_client_ip(request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the first address in X-Forwarded-For (client origin)
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        client = request.client
        if client is not None and client.host:
            return client.host

        return "0.0.0.0"
