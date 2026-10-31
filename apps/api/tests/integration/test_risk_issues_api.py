import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role
from app.models.audit_log import AuditLog
from tests.integration.helpers import (
    UserFactory,
    create_project,
    login_as,
)

pytestmark = pytest.mark.integration

PROJECT_CODE = "SGD-HCM-CSVC-2026"


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _record_payload(**overrides: object) -> dict[str, object]:
    return {
        "record_type": "NCR",
        "title": "Mẫu bàn ghế chưa đạt yêu cầu",
        "description": "Mẫu cần làm lại theo tiêu chí 21 mục",
        **overrides,
    }


async def _pm_with_project(client: httpx.AsyncClient, make_user: UserFactory) -> tuple[str, str]:
    await make_user(email="pm@example.com", role=Role.PM)
    token = await login_as(client, "pm@example.com")
    project_id = await create_project(client, token)
    return token, project_id


async def _create_record(
    client: httpx.AsyncClient,
    token: str,
    project_id: str,
    **overrides: object,
) -> dict[str, object]:
    response = await client.post(
        f"/api/v1/projects/{project_id}/risk-issues",
        json=_record_payload(**overrides),
        headers=_bearer(token),
    )
    assert response.status_code == 201, response.text
    body: dict[str, object] = response.json()
    return body


async def test_first_ncr_gets_project_code_prefix_and_sequence_one(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)

    # Act
    body = await _create_record(client, token, project_id)

    # Assert
    assert body["code"] == f"{PROJECT_CODE}-NCR-001"
    assert body["status"] == "OPEN"
    assert body["priority"] == "HIGH"


async def test_sequence_increments_per_record_type(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    await _create_record(client, token, project_id)

    # Act
    second_ncr = await _create_record(client, token, project_id)
    first_cr = await _create_record(
        client, token, project_id, record_type="CR", title="Đổi thiết bị"
    )

    # Assert
    assert second_ncr["code"] == f"{PROJECT_CODE}-NCR-002"
    assert first_cr["code"] == f"{PROJECT_CODE}-CR-001"


async def test_investor_cannot_create_record(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    pm_token, project_id = await _pm_with_project(client, make_user)
    investor = await make_user(email="investor@example.com", role=Role.INVESTOR)
    await client.post(
        f"/api/v1/projects/{project_id}/members",
        json={"user_id": str(investor.id), "role": Role.INVESTOR.value},
        headers=_bearer(pm_token),
    )
    investor_token = await login_as(client, "investor@example.com")

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/risk-issues",
        json=_record_payload(),
        headers=_bearer(investor_token),
    )

    # Assert
    assert response.status_code == 403


async def test_list_filters_by_record_type(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    await _create_record(client, token, project_id)
    await _create_record(client, token, project_id, record_type="RISK", title="Thiếu nhân lực")

    # Act
    response = await client.get(
        f"/api/v1/projects/{project_id}/risk-issues",
        params={"record_type": "RISK"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert [item["code"] for item in body] == [f"{PROJECT_CODE}-RISK-001"]


async def test_pm_closes_record_and_change_is_audited(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    record = await _create_record(client, token, project_id)

    # Act
    response = await client.patch(
        f"/api/v1/projects/{project_id}/risk-issues/{record['id']}",
        json={"status": "CLOSED"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "CLOSED"
    actions = (
        (
            await session.execute(
                select(AuditLog.action).where(AuditLog.action == "risk_issue.update")
            )
        )
        .scalars()
        .all()
    )
    assert actions == ["risk_issue.update"]


async def test_patch_unknown_record_returns_404(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    unknown_id = "00000000-0000-0000-0000-000000000000"

    # Act
    response = await client.patch(
        f"/api/v1/projects/{project_id}/risk-issues/{unknown_id}",
        json={"status": "CLOSED"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 404


async def test_unknown_record_type_is_rejected(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/risk-issues",
        json=_record_payload(record_type="XYZ"),
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 422
