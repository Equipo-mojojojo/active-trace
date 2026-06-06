from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.perfil import MODALIDADES_VALIDAS

CAMPOS_EDITABLES = {
    "nombre", "apellidos", "banco", "cbu", "alias_cbu",
    "regional", "legajo_profesional", "facturador", "modalidad_cobro",
}


class PerfilConflictError(RuntimeError):
    pass


class PerfilNotFoundError(LookupError):
    pass


def validar_campos_perfil(payload: dict) -> None:
    """Pure function: raise ValueError if payload contains immutable fields."""
    if "cuil" in payload:
        raise ValueError("cuil no es editable por el usuario")
    if "modalidad_cobro" in payload and payload["modalidad_cobro"] not in MODALIDADES_VALIDAS:
        raise ValueError(f"modalidad_cobro debe ser uno de: {MODALIDADES_VALIDAS}")


class PerfilService:
    def __init__(self, session: AsyncSession, tenant_id: UUID | str):
        self.session = session
        self.tenant_id = UUID(str(tenant_id))
        self._repo = UsuarioRepository(session, tenant_id)

    async def get_perfil(self, user_id: UUID) -> Usuario:
        usuario = await self._repo.get_by_id(user_id)
        if usuario is None:
            raise PerfilNotFoundError("usuario_not_found")
        return usuario

    async def update_perfil(self, user_id: UUID, payload: dict) -> Usuario:
        validar_campos_perfil(payload)
        usuario = await self._repo.get_by_id(user_id)
        if usuario is None:
            raise PerfilNotFoundError("usuario_not_found")
        for campo, valor in payload.items():
            if campo in CAMPOS_EDITABLES and valor is not None:
                setattr(usuario, campo, valor)
        await self.session.flush()
        await self.session.refresh(usuario)
        return usuario
