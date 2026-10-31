import httpx
import pytest

from app.core.rbac import Role
from tests.integration.helpers import (
    CONTRACT_PAYLOAD,
    UserFactory,
    create_contract,
    create_project,
    login_as,
)

pytestmark = pytest.mark.integration

RULE_PAYLOAD = {"rate_per_day": "0.001", "cap_percent": "8.00", "effective_from": "2000-01-01"}
PAST_BASELINE_END = "2000-01-10"


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _pm_with_project(client: httpx.AsyncClient, make_user: UserFactory) -> tuple[str, str]:
    await make_user(email="pm@example.com", role=Role.PM)
    token = await login_as(client, "pm@example.com")
    project_id = await create_project(client, token)
    return token, project_id


async def _create_overdue_milestone(
    client: httpx.AsyncClient,
    token: str,
    project_id: str,
) -> str:
    response = await client.post(
        f"/api/v1/projects/{project_id}/milestones",
        json={
            "code": "M1",
            "name": "Khảo sát",
            "baseline_end": PAST_BASELINE_END,
            "is_hard_deadline": False,
        },
        headers=_bearer(token),
    )
    assert response.status_code == 201, response.text
    milestone_id: str = response.json()["id"]
    return milestone_id


async def test_penalty_is_capped_at_cap_percent_of_contract_value(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    contract_id = await create_contract(client, token, project_id)
    milestone_id = await _create_overdue_milestone(client, token, project_id)
    await client.post(
        f"/api/v1/projects/{project_id}/penalty-rules",
        json=RULE_PAYLOAD,
        headers=_bearer(token),
    )

    # Act
    response = await client.get(
        f"/api/v1/projects/{project_id}/milestones/{milestone_id}/penalty",
        params={"contract_id": contract_id},
        headers=_bearer(token),
    )

    # Assert
    contract_value = float(CONTRACT_PAYLOAD["contract_value"])
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["slippage_days"] > 0
    assert float(body["amount"]) == pytest.approx(contract_value * 0.08, rel=1e-9)


async def test_penalty_requires_an_effective_rule(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    contract_id = await create_contract(client, token, project_id)
    milestone_id = await _create_overdue_milestone(client, token, project_id)

    # Act
    response = await client.get(
        f"/api/v1/projects/{project_id}/milestones/{milestone_id}/penalty",
        params={"contract_id": contract_id},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 422
    assert "ngưỡng phạt" in response.json()["detail"].lower()


async def test_penalty_rejects_contract_from_another_project(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    milestone_id = await _create_overdue_milestone(client, token, project_id)
    await client.post(
        f"/api/v1/projects/{project_id}/penalty-rules",
        json=RULE_PAYLOAD,
        headers=_bearer(token),
    )
    other_project_id = await create_project(client, token, code="SGD-LD-TB10-2026")
    other_contract_id = await create_contract(client, token, other_project_id)

    # Act
    response = await client.get(
        f"/api/v1/projects/{project_id}/milestones/{milestone_id}/penalty",
        params={"contract_id": other_contract_id},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 404


async def test_rule_with_duplicate_effective_date_returns_409(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    await client.post(
        f"/api/v1/projects/{project_id}/penalty-rules",
        json=RULE_PAYLOAD,
        headers=_bearer(token),
    )

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/penalty-rules",
        json=RULE_PAYLOAD,
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 409
