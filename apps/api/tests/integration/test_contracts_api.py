import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role
from app.models.audit_log import AuditLog
from tests.integration.helpers import (
    CONTRACT_PAYLOAD,
    UserFactory,
    create_project,
    login_as,
)

pytestmark = pytest.mark.integration

MISSING_PROJECT_ID = "00000000-0000-0000-0000-000000000000"


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _pm_with_project(client: httpx.AsyncClient, make_user: UserFactory) -> tuple[str, str]:
    await make_user(email="pm@example.com", role=Role.PM)
    token = await login_as(client, "pm@example.com")
    project_id = await create_project(client, token)
    return token, project_id


async def test_pm_adds_contract_to_project(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/contracts",
        json=CONTRACT_PAYLOAD,
        headers=_bearer(token),
    )

    # Assert
    body = response.json()
    assert response.status_code == 201
    assert body["contract_number"] == "29/HĐKT-DVN"
    assert body["contract_value"] == "4848186000.00"
    assert body["expiration_date"] == "2026-06-01"


async def test_non_positive_contract_value_returns_422(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/contracts",
        json={**CONTRACT_PAYLOAD, "contract_value": "0"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 422


async def test_expiration_before_signed_date_returns_422(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/contracts",
        json={**CONTRACT_PAYLOAD, "expiration_date": "2026-01-01"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 422


async def test_list_returns_contracts_of_the_project(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    url = f"/api/v1/projects/{project_id}/contracts"
    await client.post(url, json=CONTRACT_PAYLOAD, headers=_bearer(token))
    await client.post(
        url,
        json={**CONTRACT_PAYLOAD, "package_name": "Gói TVGS", "contract_number": "TVGS-01"},
        headers=_bearer(token),
    )

    # Act
    response = await client.get(url, headers=_bearer(token))

    # Assert
    assert response.status_code == 200
    assert sorted(item["package_name"] for item in response.json()) == [
        "Gói TVGS",
        "Gói thầu chính: Thiết bị và phần mềm lớp 10",
    ]


async def test_contract_for_unknown_project_returns_404(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    await make_user(email="pm@example.com", role=Role.PM)
    token = await login_as(client, "pm@example.com")

    # Act
    response = await client.post(
        f"/api/v1/projects/{MISSING_PROJECT_ID}/contracts",
        json=CONTRACT_PAYLOAD,
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 404


async def test_contract_creation_is_audited(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)

    # Act
    await client.post(
        f"/api/v1/projects/{project_id}/contracts",
        json=CONTRACT_PAYLOAD,
        headers=_bearer(token),
    )

    # Assert
    audited = (
        await session.execute(select(AuditLog).where(AuditLog.action == "contract.create"))
    ).scalar_one()
    assert audited.changes == {"contract_number": "29/HĐKT-DVN"}
