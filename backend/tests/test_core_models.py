from __future__ import annotations

from uuid import UUID

import pytest
from sqlalchemy import text

from app.models.tenant import Tenant
from app.repositories.base import TenantScopedRepository
from tests.support_models import TenantScopedFixtureModel


@pytest.mark.asyncio
async def test_tenant_model_persists_uuid_and_timestamps(db_session):
    tenant = Tenant(slug="tenant-a", name="Tenant A")
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)

    original_updated_at = tenant.updated_at
    tenant.name = "Tenant A Updated"
    await db_session.commit()
    await db_session.refresh(tenant)

    assert isinstance(tenant.id, UUID)
    assert tenant.created_at is not None
    assert tenant.updated_at is not None
    assert tenant.updated_at >= original_updated_at
    assert tenant.deleted_at is None


@pytest.mark.asyncio
async def test_tenant_scoped_repository_isolates_tenants_and_soft_deletes(db_session):
    tenant_a = Tenant(slug="tenant-a", name="Tenant A")
    tenant_b = Tenant(slug="tenant-b", name="Tenant B")
    db_session.add_all([tenant_a, tenant_b])
    await db_session.commit()
    await db_session.refresh(tenant_a)
    await db_session.refresh(tenant_b)

    repository_a = TenantScopedRepository(
        db_session, TenantScopedFixtureModel, tenant_a.id
    )
    repository_b = TenantScopedRepository(
        db_session, TenantScopedFixtureModel, tenant_b.id
    )

    record_a = await repository_a.create(name="Record A", secret_value="alpha-secret")
    record_b = await repository_b.create(name="Record B", secret_value="beta-secret")
    await db_session.commit()

    visible_to_a = await repository_a.list_all()
    record_from_b = await repository_a.get_by_id(record_b.id)

    assert [record.name for record in visible_to_a] == ["Record A"]
    assert record_from_b is None
    assert await repository_a.get_by_id(record_a.id) is not None

    deleted_record = await repository_a.soft_delete(record_a.id)
    await db_session.commit()

    assert deleted_record is not None
    assert deleted_record.deleted_at is not None
    assert await repository_a.get_by_id(record_a.id) is None
    assert len(await repository_a.list_all()) == 0
    assert len(await repository_a.list_all(include_deleted=True)) == 1


@pytest.mark.asyncio
async def test_encrypted_string_round_trip_and_raw_storage(db_session):
    tenant = Tenant(slug="tenant-c", name="Tenant C")
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)

    repository = TenantScopedRepository(db_session, TenantScopedFixtureModel, tenant.id)
    record = await repository.create(name="Encrypted", secret_value="dni-12345678")
    await db_session.commit()
    await db_session.refresh(record)

    raw_value = (
        await db_session.execute(
            text(
                "SELECT secret_value FROM tenant_scoped_fixture_model WHERE id = :record_id"
            ),
            {"record_id": record.id},
        )
    ).scalar_one()

    assert record.secret_value == "dni-12345678"
    assert raw_value != "dni-12345678"
