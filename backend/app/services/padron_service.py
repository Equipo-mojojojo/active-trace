"""
PadronService: Business logic for roster (padrón) management.

Orchestrates PadronRepository, PadronParser, MoodleWSClient, and AuditService.
All identity comes from the actor parameter — never from request params.

Design decisions applied:
  D1: Activating a new version deactivates the previous in the same transaction.
  D2: Parser is separate (padron_parser.py).
  D3: Preview is stateless (no DB writes).
  D4: MoodleWSClient is injected or defaulted.
  D5: Vaciado is scope-isolated by user role.
  D6: Email is encrypted at the model/repository level.
"""

from __future__ import annotations

import logging
from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_constants import AuditAction
from app.integrations.moodle_ws import MoodleWSClient, MoodleNotConfiguredError, MoodleWSError
from app.models.padron import VersionPadron
from app.models.user import User
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.padron_repository import PadronRepository
from app.services.audit_service import AuditService
from app.services.padron_parser import PadronParseError, get_detected_columns, parse_padron

logger = logging.getLogger(__name__)


class PadronNotFoundError(LookupError):
    """Raised when a required version or entry does not exist."""


class PadronForbiddenError(PermissionError):
    """Raised when the actor lacks scope to perform the operation (D5 / RN-04)."""


class PadronService:
    """Service for padrón import, versioning, and Moodle sync."""

    def __init__(
        self,
        session: AsyncSession,
        tenant_id: UUID | str,
        audit: AuditService | None = None,
        moodle_client: MoodleWSClient | None = None,
    ):
        self._session = session
        self._tenant_id = UUID(str(tenant_id))
        self._audit = audit
        self._moodle = moodle_client or MoodleWSClient()

    def _repo(self) -> PadronRepository:
        return PadronRepository(self._session, self._tenant_id)

    def _asig_repo(self) -> AsignacionRepository:
        return AsignacionRepository(self._session, self._tenant_id)

    # ------------------------------------------------------------------
    # Preview — no DB writes (D3)
    # ------------------------------------------------------------------

    async def preview(
        self,
        file_bytes: bytes,
        filename: str,
    ) -> dict:
        """Parse a file and return a preview dict without persisting anything.

        Returns:
            {
                alumnos: list[dict],  # with email_enmascarado instead of email
                columnas_detectadas: list[str],
                total: int,
            }

        Raises:
            PadronParseError: if file is invalid.
        """
        rows = parse_padron(file_bytes, filename)
        detected = get_detected_columns(rows)

        alumnos_preview = [
            {
                "nombre": r.get("nombre"),
                "apellidos": r.get("apellidos"),
                "email_enmascarado": _mask_email(r.get("email")),
                "comision": r.get("comision"),
                "regional": r.get("regional"),
            }
            for r in rows
        ]

        return {
            "alumnos": alumnos_preview,
            "columnas_detectadas": detected,
            "total": len(rows),
        }

    # ------------------------------------------------------------------
    # Importar — create new active version (D1)
    # ------------------------------------------------------------------

    async def importar(
        self,
        actor: User,
        materia_id: UUID,
        cohorte_id: UUID,
        file_bytes: bytes,
        filename: str,
    ) -> VersionPadron:
        """Parse file, deactivate previous version, create new active version.

        Spec requirements:
          - PROFESOR can only import for assigned materias (checked by caller/router).
          - Audit PADRON_CARGAR is registered.
          - Email encrypted at the EntradaPadron model level.

        Returns the newly created VersionPadron.

        Raises:
            PadronParseError: if file is invalid.
        """
        rows = parse_padron(file_bytes, filename)

        repo = self._repo()

        # D1: deactivate previous version atomically before inserting new one
        await repo.desactivar_version_activa(materia_id, cohorte_id)

        nueva_version = await repo.crear_version(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            cargado_by=actor.id,
            origen="archivo",
        )

        total = await repo.crear_entradas_bulk(nueva_version.id, rows)
        await repo.actualizar_total_entradas(nueva_version.id, total)
        await self._session.flush()
        await self._session.refresh(nueva_version)

        # Audit
        if self._audit:
            await self._audit.register(
                actor_id=actor.id,
                accion=AuditAction.PADRON_CARGAR,
                materia_id=materia_id,
                filas_afectadas=total,
                detalle={
                    "version_id": str(nueva_version.id),
                    "materia_id": str(materia_id),
                    "cohorte_id": str(cohorte_id),
                    "origen": "archivo",
                    "filename": filename,
                },
            )

        return nueva_version

    # ------------------------------------------------------------------
    # Vaciar — soft delete active version (D5 / RN-04)
    # ------------------------------------------------------------------

    async def vaciar(
        self,
        actor: User,
        materia_id: UUID,
        cohorte_id: UUID,
    ) -> VersionPadron:
        """Soft-delete the active version for (materia, cohorte).

        A PROFESOR can only vaciar a version if they have an active assignment
        for that materia. A COORDINADOR or ADMIN can vaciar any version in
        the tenant (global scope).

        Raises:
            PadronNotFoundError: if no active version exists.
            PadronForbiddenError: if a PROFESOR tries to vaciar a materia they
                                  don't have a vigent assignment for.
        """
        repo = self._repo()

        version = await repo.obtener_version_activa(materia_id, cohorte_id)
        if version is None:
            raise PadronNotFoundError(
                f"No existe versión activa de padrón para materia={materia_id}, "
                f"cohorte={cohorte_id}."
            )

        # Role-based scope check (D5 / RN-04)
        actor_roles: list[str] = getattr(actor, "roles", []) or []
        is_global_role = any(r in ("COORDINADOR", "ADMIN") for r in actor_roles)

        if not is_global_role:
            # PROFESOR: must have a vigent assignment for the materia
            asig_repo = self._asig_repo()
            asignaciones = await asig_repo.find_vigent_for_user(
                usuario_id=actor.id,
                tenant_id=self._tenant_id,
                rol="PROFESOR",
                today=date.today(),
            )
            has_assignment = any(a.materia_id == materia_id for a in asignaciones)
            if not has_assignment:
                raise PadronForbiddenError(
                    "Solo podés vaciar el padrón de materias en las que tenés "
                    "una asignación vigente como PROFESOR."
                )

        deleted = await repo.soft_delete_version(version.id)
        return deleted

    # ------------------------------------------------------------------
    # Listar versiones
    # ------------------------------------------------------------------

    async def listar_versiones(
        self,
        materia_id: UUID,
        cohorte_id: UUID,
    ) -> list[VersionPadron]:
        """Return all versions (active + historical) ordered by created_at DESC."""
        repo = self._repo()
        return await repo.listar_versiones(materia_id, cohorte_id)

    # ------------------------------------------------------------------
    # Sync from Moodle (on-demand) (D4)
    # ------------------------------------------------------------------

    async def sync_moodle(
        self,
        actor: User,
        materia_id: UUID,
        cohorte_id: UUID,
        moodle_course_id: str,
    ) -> VersionPadron:
        """Sync enrolled users from Moodle and create a new active version.

        Raises:
            MoodleNotConfiguredError: LMS credentials not configured.
            MoodleWSError: LMS call failed.
        """
        # May raise MoodleNotConfiguredError or MoodleWSError (propagated)
        users = await self._moodle.get_enrolled_users(moodle_course_id)

        # Convert to parser-compatible rows
        rows = [
            {
                "nombre": u.get("nombre", ""),
                "apellidos": u.get("apellidos", ""),
                "email": u.get("email"),
                "comision": None,
                "regional": None,
            }
            for u in users
        ]

        repo = self._repo()
        await repo.desactivar_version_activa(materia_id, cohorte_id)

        nueva_version = await repo.crear_version(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            cargado_by=actor.id,
            origen="moodle",
        )

        total = await repo.crear_entradas_bulk(nueva_version.id, rows)
        await repo.actualizar_total_entradas(nueva_version.id, total)
        await self._session.flush()
        await self._session.refresh(nueva_version)

        if self._audit:
            await self._audit.register(
                actor_id=actor.id,
                accion=AuditAction.PADRON_CARGAR,
                materia_id=materia_id,
                filas_afectadas=total,
                detalle={
                    "version_id": str(nueva_version.id),
                    "materia_id": str(materia_id),
                    "cohorte_id": str(cohorte_id),
                    "origen": "moodle",
                    "moodle_course_id": moodle_course_id,
                },
            )

        return nueva_version

    # ------------------------------------------------------------------
    # Sync nocturna — isolated per tenant
    # ------------------------------------------------------------------

    async def sync_nocturna_all_tenants(
        self,
        tenant_configs: list[dict],
    ) -> dict[str, list[str]]:
        """Process nocturnal sync for all configured tenants.

        tenant_configs: list of dicts with keys:
          tenant_id, materia_id, cohorte_id, moodle_course_id, actor_id.

        Returns:
          {"ok": [tenant_ids], "error": [tenant_ids]}

        Errors in one tenant do NOT interrupt processing of others (spec req).
        """
        results: dict[str, list[str]] = {"ok": [], "error": []}

        for config in tenant_configs:
            tid = str(config["tenant_id"])
            try:
                users = await self._moodle.get_enrolled_users(config["moodle_course_id"])
                rows = [
                    {
                        "nombre": u.get("nombre", ""),
                        "apellidos": u.get("apellidos", ""),
                        "email": u.get("email"),
                        "comision": None,
                        "regional": None,
                    }
                    for u in users
                ]

                repo = PadronRepository(self._session, config["tenant_id"])
                await repo.desactivar_version_activa(
                    config["materia_id"], config["cohorte_id"]
                )
                nueva = await repo.crear_version(
                    materia_id=config["materia_id"],
                    cohorte_id=config["cohorte_id"],
                    origen="moodle",
                )
                total = await repo.crear_entradas_bulk(nueva.id, rows)
                await repo.actualizar_total_entradas(nueva.id, total)
                await self._session.flush()

                results["ok"].append(tid)
                logger.info(
                    "sync_nocturna_all_tenants: tenant=%s ok entries=%d", tid, total
                )

            except (MoodleWSError, MoodleNotConfiguredError) as exc:
                results["error"].append(tid)
                logger.error(
                    "sync_nocturna_all_tenants: tenant=%s error=%s", tid, str(exc)
                )
            except Exception as exc:  # noqa: BLE001
                results["error"].append(tid)
                logger.error(
                    "sync_nocturna_all_tenants: tenant=%s unexpected_error=%s",
                    tid,
                    str(exc),
                )

        return results


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _mask_email(email: str | None) -> str | None:
    """Return a masked version of the email for preview (never plaintext)."""
    if not email:
        return None
    parts = email.split("@")
    if len(parts) != 2:
        return "***@***.***"
    local, domain = parts
    if len(local) <= 2:
        masked_local = "***"
    else:
        masked_local = local[0] + "***" + local[-1]
    return f"{masked_local}@{domain}"
