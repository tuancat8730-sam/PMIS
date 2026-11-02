from decimal import Decimal
from uuid import UUID

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role
from app.models.project_budget_item import BudgetCategory, ProjectBudgetItem
from tests.integration.helpers import UserFactory, create_project, login_as

pytestmark = pytest.mark.integration


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _budget_url(project_id: str) -> str:
    return f"/api/v1/projects/{project_id}/budget-items"


async def test_pm_lists_budget_items_in_display_order_with_amount_and_note(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    await make_user(email="pm-chi-phi@example.com", role=Role.PM)
    token = await login_as(client, "pm-chi-phi@example.com")
    project_id = await create_project(client, token)
    session.add_all(
        [
            ProjectBudgetItem(
                project_id=UUID(project_id),
                category=BudgetCategory.OTHER,
                label="Chi phí khác",
                amount=Decimal("62046379.00"),
                sort_order=3,
            ),
            ProjectBudgetItem(
                project_id=UUID(project_id),
                category=BudgetCategory.SOFTWARE,
                label="Chi phí phần mềm",
                amount=Decimal("5447400000.00"),
                note="Giá trúng HĐ 4.848.186.000 đ",
                sort_order=1,
            ),
        ]
    )
    await session.commit()

    # Act
    response = await client.get(_budget_url(project_id), headers=_bearer(token))

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert [row["category"] for row in body] == ["SOFTWARE", "OTHER"]
    assert Decimal(body[0]["amount"]) == Decimal("5447400000.00")
    assert body[0]["note"] == "Giá trúng HĐ 4.848.186.000 đ"
    assert body[1]["note"] is None


async def test_project_without_budget_items_returns_empty_list(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    await make_user(email="pm-chi-phi-trong@example.com", role=Role.PM)
    token = await login_as(client, "pm-chi-phi-trong@example.com")
    project_id = await create_project(client, token)

    # Act
    response = await client.get(_budget_url(project_id), headers=_bearer(token))

    # Assert
    assert response.status_code == 200
    assert response.json() == []
