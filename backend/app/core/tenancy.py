from __future__ import annotations

from uuid import UUID


class TenantScopeError(ValueError):
    pass


def normalize_tenant_id(tenant_id: UUID | str) -> UUID:
    if isinstance(tenant_id, UUID):
        return tenant_id

    return UUID(tenant_id)
