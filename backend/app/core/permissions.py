"""RBAC permission resolution and caching layer.

Provides the core permission checking infrastructure:
- `get_effective_permissions()` — resolves permission codes from user roles
- `require_permission()` — FastAPI dependency guard
- `has_permission_with_scope()` — helper for `:propio` scoping
- `invalidate_permission_cache()` — cache busting when assignments change
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.repositories.role_repository import RoleRepository

# ---------------------------------------------------------------------------
# Permission cache
# ---------------------------------------------------------------------------
# Simple LRU cache: key = f"{tenant_id}:{user_id}" → set[perm_code]
# No TTL — invalidated explicitly when role-permission assignments change.

_MAX_CACHE_SIZE = 1000
_permission_cache: OrderedDict[str, set[str]] = OrderedDict()


def _cache_key(tenant_id: UUID | str, user_id: UUID | str) -> str:
    return f"{tenant_id}:{user_id}"


def get_cached_permissions(tenant_id: UUID | str, user_id: UUID | str) -> set[str] | None:
    """Return cached permissions or None if not cached."""
    key = _cache_key(tenant_id, user_id)
    if key not in _permission_cache:
        return None

    _permission_cache.move_to_end(key)
    return _permission_cache[key]


def set_cached_permissions(tenant_id: UUID | str, user_id: UUID | str, perms: set[str]) -> None:
    """Store permissions in cache, evicting LRU entries if at capacity."""
    key = _cache_key(tenant_id, user_id)

    if key in _permission_cache:
        _permission_cache.move_to_end(key)
    else:
        if len(_permission_cache) >= _MAX_CACHE_SIZE:
            _permission_cache.popitem(last=False)

    _permission_cache[key] = perms


def invalidate_permission_cache(tenant_id: UUID | str, user_id: UUID | str | None = None) -> None:
    """Invalidate cached permissions.

    Args:
        tenant_id: Tenant scope.
        user_id: If provided, only invalidate that user's cache.
                 If None, invalidate ALL entries for that tenant (broadcast).
    """
    if user_id is not None:
        _permission_cache.pop(_cache_key(tenant_id, user_id), None)
        return

    prefix = f"{tenant_id}:"
    keys_to_remove = [k for k in _permission_cache if k.startswith(prefix)]
    for k in keys_to_remove:
        _permission_cache.pop(k, None)


def invalidate_permission_cache_for_role(tenant_id: UUID | str, role_nombre: str) -> None:
    """Invalidate cache entries for all users who have a specific role.

    This is a best-effort broadcast when a role's permissions change.
    Since we don't track which users have which role in the cache key,
    we invalidate all entries for the tenant.
    """
    invalidate_permission_cache(tenant_id)


def clear_all_caches() -> None:
    """Clear the entire permission cache (for testing / admin reset)."""
    _permission_cache.clear()


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


async def get_effective_permissions(
    user_id: UUID | str,
    tenant_id: UUID | str,
    db: AsyncSession,
    *,
    use_cache: bool = True,
) -> set[str]:
    """Resolve effective permission codes for a user.

    Returns the union of all permissions from all roles assigned to the user,
    scoped by tenant. Results are cached in memory unless ``use_cache=False``.
    """
    if use_cache:
        cached = get_cached_permissions(tenant_id, user_id)
        if cached is not None:
            return cached

    repository = RoleRepository(db)
    perms = await repository.get_effective_permission_codes(
        user_id=UUID(str(user_id)),
        tenant_id=UUID(str(tenant_id)),
    )

    if use_cache:
        set_cached_permissions(tenant_id, user_id, perms)

    return perms


# ---------------------------------------------------------------------------
# Scope checking for `:propio` permissions
# ---------------------------------------------------------------------------


def _perm_is_global(perm_code: str) -> bool:
    """A permission is 'global' if it does not end with ':propio'."""
    return not perm_code.endswith(":propio")


def _perm_base_code(perm_code: str) -> str:
    """Strip ':propio' suffix to get the base permission code.

    Example: ``calificaciones:importar:propio`` → ``calificaciones:importar``
    """
    if perm_code.endswith(":propio"):
        return perm_code[:-7]
    return perm_code


def _perm_propio_code(perm_code: str) -> str:
    """Add ':propio' suffix to get the scoped variant.

    Example: ``calificaciones:importar`` → ``calificaciones:importar:propio``
    """
    if perm_code.endswith(":propio"):
        return perm_code
    return f"{perm_code}:propio"


async def has_permission_with_scope(
    permiso_base: str,
    user: User,
    resource_owner_id: UUID | str,
    db: AsyncSession,
    *,
    use_cache: bool = True,
) -> bool:
    """Check if a user has a permission, considering `:propio` scoping.

    A user with the **global** variant (e.g. ``calificaciones:importar``)
    always passes. A user with only the **:propio** variant passes only if
    ``resource_owner_id`` matches the user's own ID.

    Returns:
        True if the user is authorized, False otherwise.
    """
    perms = await get_effective_permissions(
        user_id=user.id,
        tenant_id=user.tenant_id,
        db=db,
        use_cache=use_cache,
    )

    # Global variant — no scope check needed
    if permiso_base in perms:
        return True

    # :propio variant — check resource ownership
    propio_code = _perm_propio_code(permiso_base)
    if propio_code in perms:
        return UUID(str(resource_owner_id)) == user.id

    return False


# ---------------------------------------------------------------------------
# FastAPI dependency guard
# ---------------------------------------------------------------------------


class RequirePermission:
    """FastAPI dependency that checks a required permission.

    Usage::

        @router.get("/admin/roles")
        async def list_roles(
            user: User = Depends(get_current_user),
            _: None = Depends(RequirePermission("rbac:gestionar")),
            db: AsyncSession = Depends(get_db),
        ):
            ...
    """

    def __init__(self, perm_code: str):
        self.perm_code = perm_code

    async def __call__(
        self,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> None:
        try:
            perms = await get_effective_permissions(
                user_id=user.id,
                tenant_id=user.tenant_id,
                db=db,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission check failed — access denied",
            ) from exc

        # Check both the base and :propio variant
        if self.perm_code not in perms and _perm_propio_code(self.perm_code) not in perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required permission: {self.perm_code}",
            )


# Convenience function alias for the common inline use case:
#   Depends(require_permission("rbac:gestionar"))
require_permission = RequirePermission
