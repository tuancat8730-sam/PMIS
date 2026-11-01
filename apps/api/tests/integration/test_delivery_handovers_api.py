from typing import Any

import httpx
import pytest

from app.core.rbac import Role
from tests.integration.helpers import UserFactory, create_project, login_as

pytestmark = pytest.mark.integration

BATCH_SLOTS_PER_UNIT = 4


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _unit(unit_code: str, cluster_code: str) -> dict[str, Any]:
    return {
        "unit_code": unit_code,
        "official_name": f"Trường {unit_code}",
        "former_name": None,
        "unit_type": "THPT",
        "cluster_code": cluster_code,
        "cluster_name": cluster_code,
    }


async def _pm_with_two_units(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> tuple[str, str]:
    await make_user(email="pm@example.com", role=Role.PM)
    token = await login_as(client, "pm@example.com")
    project_id = await create_project(client, token)
    for unit_code, cluster_code in (("LD-01", "LD-1"), ("LD-02", "LD-2")):
        response = await client.post(
            f"/api/v1/projects/{project_id}/beneficiary-units",
            json=_unit(unit_code, cluster_code),
            headers=_bearer(token),
        )
        assert response.status_code == 201
    return token, project_id


async def _generate(client: httpx.AsyncClient, token: str, project_id: str) -> httpx.Response:
    return await client.post(
        f"/api/v1/projects/{project_id}/delivery-handovers/generate",
        headers=_bearer(token),
    )


async def test_generate_creates_one_row_per_unit_per_batch_plus_overall(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_two_units(client, make_user)

    # Act
    response = await _generate(client, token, project_id)

    # Assert
    assert response.status_code == 201
    assert response.json()["created"] == 2 * BATCH_SLOTS_PER_UNIT


async def test_generate_twice_creates_no_duplicates(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_two_units(client, make_user)
    await _generate(client, token, project_id)

    # Act
    response = await _generate(client, token, project_id)

    # Assert
    assert response.json()["created"] == 0


async def test_generate_without_units_is_rejected(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    await make_user(email="pm@example.com", role=Role.PM)
    token = await login_as(client, "pm@example.com")
    project_id = await create_project(client, token)

    # Act
    response = await _generate(client, token, project_id)

    # Assert
    assert response.status_code == 422


async def test_list_filters_by_cluster_code(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_two_units(client, make_user)
    await _generate(client, token, project_id)

    # Act
    response = await client.get(
        f"/api/v1/projects/{project_id}/delivery-handovers",
        params={"cluster_code": "LD-1"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == BATCH_SLOTS_PER_UNIT
    assert {row["cluster_code"] for row in rows} == {"LD-1"}


async def test_skipping_status_is_rejected_with_conflict(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_two_units(client, make_user)
    await _generate(client, token, project_id)
    rows = (
        await client.get(
            f"/api/v1/projects/{project_id}/delivery-handovers",
            headers=_bearer(token),
        )
    ).json()
    handover_id = rows[0]["id"]

    # Act
    response = await client.patch(
        f"/api/v1/projects/{project_id}/delivery-handovers/{handover_id}/status",
        json={"delivery_status": "INSTALLED"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 409
