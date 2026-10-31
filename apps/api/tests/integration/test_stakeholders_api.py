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


def _consortium_member(organization: str, share: str) -> dict[str, str]:
    return {
        "role": "CONSORTIUM_MEMBER",
        "organization_name": organization,
        "share_percentage": share,
        "responsibility_scope": "Phân hệ A, C, D",
    }


async def _pm_with_project(client: httpx.AsyncClient, make_user: UserFactory) -> tuple[str, str]:
    await make_user(email="pm@example.com", role=Role.PM)
    token = await login_as(client, "pm@example.com")
    project_id = await create_project(client, token)
    return token, project_id


async def test_pm_adds_stakeholder_to_project(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    payload = {"role": "INVESTOR", "organization_name": "Sở GD&ĐT TP.HCM"}

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/stakeholders", json=payload, headers=_bearer(token)
    )

    # Assert
    body = response.json()
    assert response.status_code == 201
    assert body["role"] == "INVESTOR"
    assert body["organization_name"] == "Sở GD&ĐT TP.HCM"
    assert body["share_percentage"] is None


async def test_consortium_shares_totalling_over_100_percent_return_422(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    url = f"/api/v1/projects/{project_id}/stakeholders"
    await client.post(url, json=_consortium_member("DTH", "95.00"), headers=_bearer(token))
    await client.post(url, json=_consortium_member("VietFuture", "5.00"), headers=_bearer(token))

    # Act
    response = await client.post(
        url, json=_consortium_member("Thêm", "1.00"), headers=_bearer(token)
    )

    # Assert
    assert response.status_code == 422


async def test_consortium_shares_summing_to_100_percent_are_accepted(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    url = f"/api/v1/projects/{project_id}/stakeholders"

    # Act
    first = await client.post(url, json=_consortium_member("DTH", "95.00"), headers=_bearer(token))
    second = await client.post(
        url, json=_consortium_member("VietFuture", "5.00"), headers=_bearer(token)
    )

    # Assert
    assert [first.status_code, second.status_code] == [201, 201]


async def test_stakeholder_for_unknown_project_returns_404(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    await make_user(email="pm@example.com", role=Role.PM)
    token = await login_as(client, "pm@example.com")

    # Act
    response = await client.post(
        f"/api/v1/projects/{MISSING_PROJECT_ID}/stakeholders",
        json={"role": "INVESTOR", "organization_name": "Sở GD&ĐT TP.HCM"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 404


async def test_list_returns_stakeholders_of_the_project_only(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    url = f"/api/v1/projects/{project_id}/stakeholders"
    await client.post(url, json=_consortium_member("DTH", "95.00"), headers=_bearer(token))
    await client.post(url, json=_consortium_member("VietFuture", "5.00"), headers=_bearer(token))

    # Act
    response = await client.get(url, headers=_bearer(token))

    # Assert
    assert response.status_code == 200
    assert [item["organization_name"] for item in response.json()] == ["DTH", "VietFuture"]


async def test_stakeholder_creation_is_audited_with_actor(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    pm = await make_user(email="pm@example.com", role=Role.PM)
    token = await login_as(client, "pm@example.com")
    project_id = await create_project(client, token)

    # Act
    await client.post(
        f"/api/v1/projects/{project_id}/stakeholders",
        json={"role": "INVESTOR", "organization_name": "Sở GD&ĐT TP.HCM"},
        headers=_bearer(token),
    )

    # Assert
    audited = (
        await session.execute(select(AuditLog).where(AuditLog.action == "stakeholder.create"))
    ).scalar_one()
    assert audited.actor_id == pm.id
    assert audited.changes == {"role": "INVESTOR", "organization_name": "Sở GD&ĐT TP.HCM"}


async def test_consultant_cannot_add_stakeholder(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    _, project_id = await _pm_with_project(client, make_user)
    await make_user(email="consultant@example.com", role=Role.PM_CONSULTANT)
    consultant_token = await login_as(client, "consultant@example.com")

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/stakeholders",
        json={"role": "INVESTOR", "organization_name": "Sở GD&ĐT TP.HCM"},
        headers=_bearer(consultant_token),
    )

    # Assert
    assert response.status_code == 403
