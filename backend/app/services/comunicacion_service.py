"""ComunicacionService — C-12 comunicaciones-cola-worker.

Handles preview, template rendering, enqueueing, approval, rejection, and
cancellation of outgoing communications.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import time
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_constants import AuditAction
from app.core.config import get_settings
from app.models.comunicacion import Comunicacion
from app.models.enums import EstadoComunicacion
from app.repositories.comunicacion_repository import ComunicacionRepository
from app.schemas.comunicacion import (
    ComunicacionDestinatarioDTO,
    ComunicacionEnviarRequestDTO,
    ComunicacionEnviarResponseDTO,
    ComunicacionPreviewRequestDTO,
    ComunicacionPreviewResponseDTO,
    ComunicacionResponseDTO,
    LoteResponseDTO,
)
from app.services.audit_service import AuditService

KNOWN_VARIABLES = {"nombre_alumno", "materia", "docente"}
_PREVIEW_TTL_SECONDS = 600  # 10 minutes
_VAR_PATTERN = re.compile(r"\{(\w+)\}")


class VariableDesconocidaError(ValueError):
    pass


class PreviewRequiredError(ValueError):
    pass


class PreviewExpiredError(ValueError):
    pass


class ComunicacionNotFoundError(Exception):
    pass


class ComunicacionService:
    def __init__(
        self,
        session: AsyncSession,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        self.session = session
        self._ip = ip
        self._user_agent = user_agent

    # ── Template rendering ───────────────────────────────────────────

    def _render_template(self, template: str, variables: dict[str, str]) -> str:
        unknown = {m for m in _VAR_PATTERN.findall(template)} - KNOWN_VARIABLES
        if unknown:
            raise VariableDesconocidaError(
                f"Variable(s) desconocida(s): {', '.join(sorted(unknown))}"
            )
        return template.format_map(variables)

    # ── Preview token ────────────────────────────────────────────────

    @staticmethod
    def _template_hash(asunto: str, cuerpo: str) -> str:
        return hashlib.sha256(f"{asunto}|{cuerpo}".encode()).hexdigest()[:24]

    def _generate_preview_token(
        self,
        asunto: str,
        cuerpo: str,
        *,
        issued_at_override: float | None = None,
    ) -> str:
        settings = get_settings()
        secret = settings.SECRET_KEY.get_secret_value().encode()
        payload = json.dumps(
            {
                "th": self._template_hash(asunto, cuerpo),
                "iat": issued_at_override if issued_at_override is not None else time.time(),
            }
        )
        sig = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()
        raw = json.dumps({"p": payload, "s": sig})
        return base64.urlsafe_b64encode(raw.encode()).decode()

    def _validate_preview_token(
        self, token: str | None, asunto: str, cuerpo: str
    ) -> None:
        if not token:
            raise PreviewRequiredError("Se requiere preview previo al envío")
        try:
            padded = token + "=" * (-len(token) % 4)
            raw = base64.urlsafe_b64decode(padded.encode()).decode()
            data = json.loads(raw)
            payload_str = data["p"]
            sig = data["s"]
        except Exception:
            raise PreviewRequiredError("Token de preview inválido")

        settings = get_settings()
        secret = settings.SECRET_KEY.get_secret_value().encode()
        expected = hmac.new(secret, payload_str.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(sig, expected):
            raise PreviewRequiredError("Token de preview inválido")

        payload_data = json.loads(payload_str)
        if time.time() - payload_data["iat"] > _PREVIEW_TTL_SECONDS:
            raise PreviewExpiredError("El token de preview expiró")

        if payload_data["th"] != self._template_hash(asunto, cuerpo):
            raise PreviewRequiredError("El template ha cambiado desde el preview")

    # ── Public API ───────────────────────────────────────────────────

    def preview(self, request: ComunicacionPreviewRequestDTO) -> ComunicacionPreviewResponseDTO:
        asunto_r = self._render_template(request.asunto, request.variables)
        cuerpo_r = self._render_template(request.cuerpo, request.variables)
        token = self._generate_preview_token(request.asunto, request.cuerpo)
        return ComunicacionPreviewResponseDTO(
            asunto_renderizado=asunto_r,
            cuerpo_renderizado=cuerpo_r,
            preview_token=token,
        )

    async def encolar_lote(
        self,
        request: ComunicacionEnviarRequestDTO,
        tenant_id: UUID,
        enviado_por: UUID,
    ) -> ComunicacionEnviarResponseDTO:
        self._validate_preview_token(request.preview_token, request.asunto, request.cuerpo)

        repo = ComunicacionRepository(self.session, tenant_id)
        lote_id = uuid4()

        for dest in request.destinatarios:
            await repo.crear(
                tenant_id=tenant_id,
                enviado_por=enviado_por,
                materia_id=request.materia_id,
                destinatario=dest.email,
                asunto=self._render_template(request.asunto, dest.variables),
                cuerpo=self._render_template(request.cuerpo, dest.variables),
                lote_id=lote_id,
            )

        audit = AuditService(self.session, tenant_id, self._ip, self._user_agent)
        await audit.register(
            actor_id=enviado_por,
            accion=AuditAction.COMUNICACION_ENVIAR,
            filas_afectadas=len(request.destinatarios),
        )

        await self.session.commit()
        return ComunicacionEnviarResponseDTO(lote_id=lote_id, count=len(request.destinatarios))

    async def cancelar(
        self, comunicacion_id: UUID, actor_id: UUID, tenant_id: UUID
    ) -> None:
        repo = ComunicacionRepository(self.session, tenant_id)
        m = await repo.get(comunicacion_id)
        if m is None:
            raise ComunicacionNotFoundError(str(comunicacion_id))
        m.cancelar()
        await self.session.flush()

        audit = AuditService(self.session, tenant_id, self._ip, self._user_agent)
        await audit.register(actor_id=actor_id, accion=AuditAction.COMUNICACION_CANCELAR)
        await self.session.commit()

    async def aprobar_lote(
        self, lote_id: UUID, actor_id: UUID, tenant_id: UUID
    ) -> LoteResponseDTO:
        repo = ComunicacionRepository(self.session, tenant_id)
        count = await repo.aprobar_lote(lote_id, aprobado_por=actor_id)

        audit = AuditService(self.session, tenant_id, self._ip, self._user_agent)
        await audit.register(
            actor_id=actor_id,
            accion=AuditAction.COMUNICACION_APROBAR,
            filas_afectadas=count,
        )
        await self.session.commit()

        mensajes = await repo.listar_por_lote(lote_id)
        return LoteResponseDTO(
            lote_id=lote_id,
            mensajes=[ComunicacionResponseDTO.model_validate(m) for m in mensajes],
            count=len(mensajes),
        )

    async def rechazar_lote(
        self, lote_id: UUID, actor_id: UUID, tenant_id: UUID
    ) -> LoteResponseDTO:
        repo = ComunicacionRepository(self.session, tenant_id)
        count = await repo.rechazar_lote(lote_id)

        audit = AuditService(self.session, tenant_id, self._ip, self._user_agent)
        await audit.register(
            actor_id=actor_id,
            accion=AuditAction.COMUNICACION_RECHAZAR,
            filas_afectadas=count,
        )
        await self.session.commit()

        mensajes = await repo.listar_por_lote(lote_id)
        return LoteResponseDTO(
            lote_id=lote_id,
            mensajes=[ComunicacionResponseDTO.model_validate(m) for m in mensajes],
            count=len(mensajes),
        )

    async def aprobar_individual(
        self, comunicacion_id: UUID, actor_id: UUID, tenant_id: UUID
    ) -> ComunicacionResponseDTO:
        repo = ComunicacionRepository(self.session, tenant_id)
        m = await repo.aprobar_individual(comunicacion_id, aprobado_por=actor_id)
        if m is None:
            raise ComunicacionNotFoundError(str(comunicacion_id))

        audit = AuditService(self.session, tenant_id, self._ip, self._user_agent)
        await audit.register(
            actor_id=actor_id,
            accion=AuditAction.COMUNICACION_APROBAR,
            filas_afectadas=1,
        )
        await self.session.commit()
        return ComunicacionResponseDTO.model_validate(m)

    async def rechazar_individual(
        self, comunicacion_id: UUID, actor_id: UUID, tenant_id: UUID
    ) -> ComunicacionResponseDTO:
        repo = ComunicacionRepository(self.session, tenant_id)
        m = await repo.rechazar_individual(comunicacion_id)
        if m is None:
            raise ComunicacionNotFoundError(str(comunicacion_id))

        audit = AuditService(self.session, tenant_id, self._ip, self._user_agent)
        await audit.register(
            actor_id=actor_id,
            accion=AuditAction.COMUNICACION_RECHAZAR,
            filas_afectadas=1,
        )
        await self.session.commit()
        return ComunicacionResponseDTO.model_validate(m)
