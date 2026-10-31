from typing import Any

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role
from app.models.audit_log import AuditLog
from tests.integration.helpers import UserFactory, create_project, login_as

pytestmark = pytest.mark.integration

MISSING_PROJECT_ID = "00000000-0000-0000-0000-000000000000"


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _unit(unit_code: str = "HCM-01", **overrides: Any) -> dict[str, Any]:
    return {
        "unit_code": unit_code,
        "official_name": "THPT Chuyên Lê Hồng Phong",
        "former_name": "THPT Lê Hồng Phong",
        "unit_type": "THPT",
        "cluster_code": "HCM-1",
        "cluster_name": "TP.HCM",
        **overrides,
    }


async def _pm_with_project(client: httpx.AsyncClient, make_user: UserFactory) -> tuple[str, str]:
    await make_user(email="pm@example.com", role=Role.PM)
    token = await login_as(client, "pm@example.com")
    project_id = await create_project(client, token)
    return token, project_id


async def _add_unit(
    client: httpx.AsyncClient, token: str, project_id: str, payload: dict[str, Any]
) -> httpx.Response:
    return await client.post(
        f"/api/v1/projects/{project_id}/beneficiary-units",
        json=payload,
        headers=_bearer(token),
    )


async def test_pm_creates_unit_with_dual_name(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)

    # Act
    response = await _add_unit(client, token, project_id, _unit())

    # Assert
    body = response.json()
    assert response.status_code == 201
    assert body["unit_code"] == "HCM-01"
    assert body["readiness_status"] == "PENDING"
    assert body["display_dual_name"] == "THPT Chuyên Lê Hồng Phong (THPT Lê Hồng Phong cũ)"


async def test_duplicate_unit_code_in_same_project_returns_409(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    await _add_unit(client, token, project_id, _unit())

    # Act
    response = await _add_unit(client, token, project_id, _unit())

    # Assert
    assert response.status_code == 409
    assert "HCM-01" in response.json()["detail"]


async def test_same_unit_code_is_allowed_in_another_project(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    other_project_id = await create_project(client, token, code="SGD-LD-TB10-2026")
    await _add_unit(client, token, project_id, _unit())

    # Act
    response = await _add_unit(client, token, other_project_id, _unit())

    # Assert
    assert response.status_code == 201


async def test_list_filters_units_by_cluster_code(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    await _add_unit(client, token, project_id, _unit("HCM-01"))
    await _add_unit(client, token, project_id, _unit("HCM-02", cluster_code="HCM-2"))

    # Act
    response = await client.get(
        f"/api/v1/projects/{project_id}/beneficiary-units",
        params={"cluster_code": "HCM-2"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 200
    assert [item["unit_code"] for item in response.json()] == ["HCM-02"]


async def test_project_member_can_read_units(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    await _add_unit(client, token, project_id, _unit())
    consultant = await make_user(email="tv@example.com", role=Role.PM_CONSULTANT)
    await client.post(
        f"/api/v1/projects/{project_id}/members",
        json={"user_id": str(consultant.id), "role": "PM_CONSULTANT"},
        headers=_bearer(token),
    )
    consultant_token = await login_as(client, "tv@example.com")

    # Act
    response = await client.get(
        f"/api/v1/projects/{project_id}/beneficiary-units",
        headers=_bearer(consultant_token),
    )

    # Assert
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_non_member_cannot_create_unit(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    _, project_id = await _pm_with_project(client, make_user)
    await make_user(email="tv@example.com", role=Role.PM_CONSULTANT)
    consultant_token = await login_as(client, "tv@example.com")

    # Act
    response = await _add_unit(client, consultant_token, project_id, _unit())

    # Assert
    assert response.status_code == 403


async def test_unit_for_unknown_project_returns_404(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, _ = await _pm_with_project(client, make_user)

    # Act
    response = await _add_unit(client, token, MISSING_PROJECT_ID, _unit())

    # Assert
    assert response.status_code == 404


async def test_unit_creation_is_audited_with_actor(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    pm = await make_user(email="pm@example.com", role=Role.PM)
    token = await login_as(client, "pm@example.com")
    project_id = await create_project(client, token)

    # Act
    await _add_unit(client, token, project_id, _unit())

    # Assert
    audited = (
        await session.execute(select(AuditLog).where(AuditLog.action == "beneficiary_unit.create"))
    ).scalar_one()
    assert audited.actor_id == pm.id
    assert audited.changes is not None
    assert audited.changes["unit_code"] == "HCM-01"


async def test_patch_updates_official_name_and_audits_the_change(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    created = (await _add_unit(client, token, project_id, _unit())).json()

    # Act
    response = await client.patch(
        f"/api/v1/projects/{project_id}/beneficiary-units/{created['id']}",
        json={"official_name": "THPT Lê Hồng Phong (mới)"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["official_name"] == "THPT Lê Hồng Phong (mới)"
    audited = (
        await session.execute(select(AuditLog).where(AuditLog.action == "beneficiary_unit.update"))
    ).scalar_one()
    assert audited.changes == {"official_name": "THPT Lê Hồng Phong (mới)"}


async def test_get_unit_returns_unit_and_404_for_other_project(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    created = (await _add_unit(client, token, project_id, _unit())).json()
    other_project_id = await create_project(client, token, code="SGD-LD-TB10-2026")

    # Act
    found = await client.get(
        f"/api/v1/projects/{project_id}/beneficiary-units/{created['id']}",
        headers=_bearer(token),
    )
    not_in_project = await client.get(
        f"/api/v1/projects/{other_project_id}/beneficiary-units/{created['id']}",
        headers=_bearer(token),
    )

    # Assert
    assert found.status_code == 200
    assert found.json()["unit_code"] == "HCM-01"
    assert not_in_project.status_code == 404


async def test_unit_with_unknown_field_is_rejected(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)

    # Act
    response = await _add_unit(client, token, project_id, _unit(readiness_override="ACCEPTED"))

    # Assert
    assert response.status_code == 422
