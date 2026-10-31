import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role
from app.models.audit_log import AuditLog
from app.models.contract_personnel import ContractPersonnel
from tests.integration.helpers import (
    UserFactory,
    create_contract,
    create_project,
    login_as,
)

pytestmark = pytest.mark.integration

MISSING_CONTRACT_ID = "00000000-0000-0000-0000-000000000000"
CCCD = "001085012345"
PERSONNEL_PAYLOAD = {
    "full_name": "Nguyễn Quang Hân",
    "organization": "DTH",
    "position_role": "Chủ nhiệm dự án",
    "national_id_cccd": CCCD,
    "qualification": "Thạc sĩ CNTT",
}


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _pm_with_contract(client: httpx.AsyncClient, make_user: UserFactory) -> tuple[str, str]:
    await make_user(email="pm@example.com", role=Role.PM)
    token = await login_as(client, "pm@example.com")
    project_id = await create_project(client, token)
    contract_id = await create_contract(client, token, project_id)
    return token, contract_id


async def test_pm_adds_personnel_and_response_hides_full_cccd(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, contract_id = await _pm_with_contract(client, make_user)

    # Act
    response = await client.post(
        f"/api/v1/contracts/{contract_id}/personnel",
        json=PERSONNEL_PAYLOAD,
        headers=_bearer(token),
    )

    # Assert
    body = response.json()
    assert response.status_code == 201
    assert body["national_id_masked"] == "********2345"
    assert body["compliance_status"] == "VERIFIED"
    assert CCCD not in response.text


async def test_cccd_is_stored_encrypted_with_last_four_digits(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    token, contract_id = await _pm_with_contract(client, make_user)

    # Act
    await client.post(
        f"/api/v1/contracts/{contract_id}/personnel",
        json=PERSONNEL_PAYLOAD,
        headers=_bearer(token),
    )

    # Assert
    stored = (await session.execute(select(ContractPersonnel))).scalar_one()
    assert stored.national_id_encrypted is not None
    assert CCCD not in stored.national_id_encrypted
    assert stored.national_id_last4 == "2345"


async def test_same_cccd_elsewhere_in_project_is_flagged_as_duplicate(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    await make_user(email="pm@example.com", role=Role.PM)
    token = await login_as(client, "pm@example.com")
    project_id = await create_project(client, token)
    first_contract_id = await create_contract(client, token, project_id)
    second_contract_id = await create_contract(client, token, project_id)
    await client.post(
        f"/api/v1/contracts/{first_contract_id}/personnel",
        json=PERSONNEL_PAYLOAD,
        headers=_bearer(token),
    )

    # Act
    response = await client.post(
        f"/api/v1/contracts/{second_contract_id}/personnel",
        json={**PERSONNEL_PAYLOAD, "full_name": "Nguyễn Đình Đạt"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 201
    assert response.json()["compliance_status"] == "DUPLICATE_ID_WARNING"


async def test_same_cccd_in_other_project_is_not_flagged(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, first_contract_id = await _pm_with_contract(client, make_user)
    await client.post(
        f"/api/v1/contracts/{first_contract_id}/personnel",
        json=PERSONNEL_PAYLOAD,
        headers=_bearer(token),
    )
    other_project_id = await create_project(client, token, code="SGD-LD-TB10-2026")
    other_contract_id = await create_contract(client, token, other_project_id)

    # Act
    response = await client.post(
        f"/api/v1/contracts/{other_contract_id}/personnel",
        json=PERSONNEL_PAYLOAD,
        headers=_bearer(token),
    )

    # Assert
    assert response.json()["compliance_status"] == "VERIFIED"


async def test_cccd_that_is_not_twelve_digits_returns_422(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, contract_id = await _pm_with_contract(client, make_user)

    # Act
    response = await client.post(
        f"/api/v1/contracts/{contract_id}/personnel",
        json={**PERSONNEL_PAYLOAD, "national_id_cccd": "12345"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 422


async def test_list_returns_only_masked_cccd(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, contract_id = await _pm_with_contract(client, make_user)
    await client.post(
        f"/api/v1/contracts/{contract_id}/personnel",
        json=PERSONNEL_PAYLOAD,
        headers=_bearer(token),
    )

    # Act
    response = await client.get(
        f"/api/v1/contracts/{contract_id}/personnel", headers=_bearer(token)
    )

    # Assert
    assert response.status_code == 200
    assert response.json()[0]["national_id_masked"] == "********2345"
    assert CCCD not in response.text


async def test_audit_log_does_not_contain_cccd(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    token, contract_id = await _pm_with_contract(client, make_user)

    # Act
    await client.post(
        f"/api/v1/contracts/{contract_id}/personnel",
        json=PERSONNEL_PAYLOAD,
        headers=_bearer(token),
    )

    # Assert
    audited = (
        await session.execute(select(AuditLog).where(AuditLog.action == "personnel.create"))
    ).scalar_one()
    assert CCCD not in str(audited.changes)


async def test_consultant_cannot_read_personnel(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, contract_id = await _pm_with_contract(client, make_user)
    await make_user(email="consultant@example.com", role=Role.PM_CONSULTANT)
    consultant_token = await login_as(client, "consultant@example.com")

    # Act
    response = await client.get(
        f"/api/v1/contracts/{contract_id}/personnel", headers=_bearer(consultant_token)
    )

    # Assert
    assert response.status_code == 403


async def test_personnel_for_unknown_contract_returns_404(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, _ = await _pm_with_contract(client, make_user)

    # Act
    response = await client.post(
        f"/api/v1/contracts/{MISSING_CONTRACT_ID}/personnel",
        json=PERSONNEL_PAYLOAD,
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 404
