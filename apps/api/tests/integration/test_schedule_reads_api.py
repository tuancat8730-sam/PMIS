import httpx
import pytest

from app.core.rbac import Role
from tests.integration.helpers import (
    UserFactory,
    create_project,
    login_as,
)

pytestmark = pytest.mark.integration

EVIDENCE_REF = "Biên bản xác nhận điểm dừng H1 số 01/BB-2026"
PAST_BASELINE_END = "2000-01-10"
FAR_FUTURE_END = "2099-12-31"
RULE_PAYLOAD = {"rate_per_day": "0.001", "cap_percent": "8.00", "effective_from": "2000-01-01"}


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _pm_with_project(client: httpx.AsyncClient, make_user: UserFactory) -> tuple[str, str]:
    await make_user(email="pm@example.com", role=Role.PM)
    token = await login_as(client, "pm@example.com")
    project_id = await create_project(client, token)
    return token, project_id


async def _member_token(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    pm_token: str,
    project_id: str,
    email: str,
    role: Role,
) -> str:
    user = await make_user(email=email, role=role)
    await client.post(
        f"/api/v1/projects/{project_id}/members",
        json={"user_id": str(user.id), "role": role.value},
        headers=_bearer(pm_token),
    )
    return await login_as(client, email)


async def test_list_milestones_returns_derived_status_for_each_milestone(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    await client.post(
        f"/api/v1/projects/{project_id}/milestones",
        json={"code": "M1", "name": "Khảo sát", "baseline_end": PAST_BASELINE_END},
        headers=_bearer(token),
    )

    # Act
    response = await client.get(f"/api/v1/projects/{project_id}/milestones", headers=_bearer(token))

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert [item["code"] for item in body] == ["M1"]
    assert body[0]["display_status"] == "OVERDUE"


async def test_get_unknown_milestone_returns_404(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    unknown_id = "00000000-0000-0000-0000-000000000000"

    # Act
    response = await client.get(
        f"/api/v1/projects/{project_id}/milestones/{unknown_id}",
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 404


async def test_completing_milestone_succeeds_once_all_three_parties_confirm(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    pm_token, project_id = await _pm_with_project(client, make_user)
    milestone = await client.post(
        f"/api/v1/projects/{project_id}/milestones",
        json={"code": "M2", "name": "Thiết kế", "baseline_end": FAR_FUTURE_END},
        headers=_bearer(pm_token),
    )
    milestone_id = milestone.json()["id"]
    hold_point = await client.post(
        f"/api/v1/projects/{project_id}/hold-points",
        json={"code": "H1", "name": "Điểm dừng H1", "milestone_id": milestone_id},
        headers=_bearer(pm_token),
    )
    hold_point_id = hold_point.json()["id"]
    supervisor_token = await _member_token(
        client, make_user, pm_token, project_id, "tvgs@example.com", Role.SUPERVISION_CONSULTANT
    )
    contractor_token = await _member_token(
        client, make_user, pm_token, project_id, "contractor@example.com", Role.CONTRACTOR
    )
    confirm_url = f"/api/v1/projects/{project_id}/hold-points/{hold_point_id}/confirmations"
    for token, party in (
        (pm_token, "CDT"),
        (supervisor_token, "TVGS"),
        (contractor_token, "NHA_THAU"),
    ):
        await client.post(
            confirm_url,
            json={"party": party, "evidence_ref": EVIDENCE_REF},
            headers=_bearer(token),
        )

    # Act
    response = await client.patch(
        f"/api/v1/projects/{project_id}/milestones/{milestone_id}",
        json={"status": "COMPLETED", "actual_end": "2026-10-30"},
        headers=_bearer(pm_token),
    )

    # Assert
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "COMPLETED"
    assert response.json()["display_status"] == "COMPLETED"


async def test_patch_rejects_null_status(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    milestone = await client.post(
        f"/api/v1/projects/{project_id}/milestones",
        json={"code": "M3", "name": "Bàn giao", "baseline_end": FAR_FUTURE_END},
        headers=_bearer(token),
    )

    # Act
    response = await client.patch(
        f"/api/v1/projects/{project_id}/milestones/{milestone.json()['id']}",
        json={"status": None},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 422


async def test_list_hold_points_shows_missing_parties(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    hold_point = await client.post(
        f"/api/v1/projects/{project_id}/hold-points",
        json={"code": "H2", "name": "Điểm dừng H2"},
        headers=_bearer(token),
    )
    await client.post(
        f"/api/v1/projects/{project_id}/hold-points/{hold_point.json()['id']}/confirmations",
        json={"party": "CDT", "evidence_ref": EVIDENCE_REF},
        headers=_bearer(token),
    )

    # Act
    response = await client.get(
        f"/api/v1/projects/{project_id}/hold-points", headers=_bearer(token)
    )

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body[0]["confirmed_parties"] == ["CDT"]
    assert body[0]["missing_parties"] == ["NHA_THAU", "TVGS"]
    assert body[0]["cleared"] is False


async def test_hold_point_linked_to_milestone_of_another_project_is_rejected(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    other_project_id = await create_project(client, token, code="SGD-LD-TB10-2026")
    other_milestone = await client.post(
        f"/api/v1/projects/{other_project_id}/milestones",
        json={"code": "M1", "name": "Khác dự án", "baseline_end": FAR_FUTURE_END},
        headers=_bearer(token),
    )

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/hold-points",
        json={"code": "H4", "name": "Điểm dừng H4", "milestone_id": other_milestone.json()["id"]},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 422


async def test_list_penalty_rules_returns_created_rules(
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
    response = await client.get(
        f"/api/v1/projects/{project_id}/penalty-rules", headers=_bearer(token)
    )

    # Assert
    assert response.status_code == 200
    assert response.json()[0]["cap_percent"] == "8.00"


async def test_penalty_rule_rejects_cap_above_100_percent(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/penalty-rules",
        json={**RULE_PAYLOAD, "cap_percent": "150.00"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 422


async def test_penalty_for_unknown_milestone_returns_404(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    unknown_id = "00000000-0000-0000-0000-000000000000"
    contract_id = "00000000-0000-0000-0000-000000000001"

    # Act
    response = await client.get(
        f"/api/v1/projects/{project_id}/milestones/{unknown_id}/penalty",
        params={"contract_id": contract_id},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 404
