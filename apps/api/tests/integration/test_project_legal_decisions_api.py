from datetime import date
from decimal import Decimal
from uuid import UUID

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role
from app.models.project_legal_decision import LegalDecisionKind, ProjectLegalDecision
from tests.integration.helpers import UserFactory, create_project, login_as

pytestmark = pytest.mark.integration


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _decisions_url(project_id: str) -> str:
    return f"/api/v1/projects/{project_id}/legal-decisions"


async def _pm_with_project(client: httpx.AsyncClient, make_user: UserFactory) -> tuple[str, str]:
    await make_user(email="pm-quyet-dinh@example.com", role=Role.PM)
    token = await login_as(client, "pm-quyet-dinh@example.com")
    project_id = await create_project(client, token)
    return token, project_id


async def _add_decisions(session: AsyncSession, project_id: str) -> None:
    session.add_all(
        [
            ProjectLegalDecision(
                project_id=UUID(project_id),
                kind=LegalDecisionKind.KHLCNT_APPROVAL,
                decision_no="1889/QĐ-SGDĐT",
                decision_date=date(2026, 6, 12),
                issuing_authority="Sở GD&ĐT",
            ),
            ProjectLegalDecision(
                project_id=UUID(project_id),
                kind=LegalDecisionKind.PROJECT_APPROVAL,
                decision_no="1595/QĐ-SGDĐT",
                decision_date=date(2026, 5, 22),
                issuing_authority="Sở GD&ĐT",
                amount=Decimal("5999498939.00"),
                funding_source="Ngân sách nhà nước",
                execution_period="2026 - 2027",
            ),
        ]
    )
    await session.commit()


async def test_pm_lists_decisions_ordered_by_date_with_amount(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    await _add_decisions(session, project_id)

    # Act
    response = await client.get(_decisions_url(project_id), headers=_bearer(token))

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert [row["decision_no"] for row in body] == ["1595/QĐ-SGDĐT", "1889/QĐ-SGDĐT"]
    assert Decimal(body[0]["amount"]) == Decimal("5999498939.00")
    assert body[0]["funding_source"] == "Ngân sách nhà nước"
    assert body[1]["amount"] is None


async def test_contractor_member_can_read_decisions(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    pm_token, project_id = await _pm_with_project(client, make_user)
    contractor = await make_user(email="nha-thau-quyet-dinh@example.com", role=Role.CONTRACTOR)
    await client.post(
        f"/api/v1/projects/{project_id}/members",
        json={"user_id": str(contractor.id), "role": Role.CONTRACTOR.value},
        headers=_bearer(pm_token),
    )
    contractor_token = await login_as(client, "nha-thau-quyet-dinh@example.com")

    # Act
    response = await client.get(_decisions_url(project_id), headers=_bearer(contractor_token))

    # Assert
    assert response.status_code == 200
    assert response.json() == []


async def test_non_member_cannot_read_decisions(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    _, project_id = await _pm_with_project(client, make_user)
    await make_user(email="nguoi-ngoai-quyet-dinh@example.com", role=Role.PM)
    outsider_token = await login_as(client, "nguoi-ngoai-quyet-dinh@example.com")

    # Act
    response = await client.get(_decisions_url(project_id), headers=_bearer(outsider_token))

    # Assert
    assert response.status_code == 403
