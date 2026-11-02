import httpx
import pytest

from app.core.rbac import Role
from tests.integration.helpers import UserFactory, create_project, login_as

pytestmark = pytest.mark.integration

FAR_FUTURE_END = "2099-12-31"


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _pm_with_project(client: httpx.AsyncClient, make_user: UserFactory) -> tuple[str, str]:
    await make_user(email="pm@example.com", role=Role.PM)
    token = await login_as(client, "pm@example.com")
    project_id = await create_project(client, token)
    return token, project_id


async def _create_milestone(
    client: httpx.AsyncClient, token: str, project_id: str, **overrides: object
) -> dict[str, object]:
    payload: dict[str, object] = {
        "code": "M1",
        "name": "Giao hàng đợt 1",
        "baseline_end": FAR_FUTURE_END,
        **overrides,
    }
    response = await client.post(
        f"/api/v1/projects/{project_id}/milestones", json=payload, headers=_bearer(token)
    )
    assert response.status_code == 201, response.text
    body: dict[str, object] = response.json()
    return body


async def _create_risk(
    client: httpx.AsyncClient, token: str, project_id: str, **overrides: object
) -> dict[str, object]:
    payload: dict[str, object] = {
        "record_type": "RISK",
        "title": "Dữ liệu nguồn chậm",
        "description": "Trường chưa gửi dữ liệu mẫu",
        **overrides,
    }
    response = await client.post(
        f"/api/v1/projects/{project_id}/risk-issues", json=payload, headers=_bearer(token)
    )
    assert response.status_code == 201, response.text
    body: dict[str, object] = response.json()
    return body


async def test_milestone_stores_tracking_fields(
    client: httpx.AsyncClient, make_user: UserFactory
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)

    # Act
    body = await _create_milestone(
        client,
        token,
        project_id,
        deliverables="Biên bản bàn giao 60 đơn vị",
        acceptance_conditions="CO, CQ đủ theo lô hàng",
        tvgs_checkpoint="W1: kiểm tra kho",
        pm_comment="Chờ serial",
    )

    # Assert
    assert body["deliverables"] == "Biên bản bàn giao 60 đơn vị"
    assert body["acceptance_conditions"] == "CO, CQ đủ theo lô hàng"
    assert body["tvgs_checkpoint"] == "W1: kiểm tra kho"
    assert body["pm_comment"] == "Chờ serial"


async def test_milestone_update_changes_pm_comment(
    client: httpx.AsyncClient, make_user: UserFactory
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    milestone = await _create_milestone(client, token, project_id)

    # Act
    response = await client.patch(
        f"/api/v1/projects/{project_id}/milestones/{milestone['id']}",
        json={"pm_comment": "Đã nhận đủ serial", "reason": "Cập nhật ghi chú PM"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 200, response.text
    assert response.json()["pm_comment"] == "Đã nhận đủ serial"


async def test_risk_stores_impact_likelihood_and_units(
    client: httpx.AsyncClient, make_user: UserFactory
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)

    # Act
    body = await _create_risk(
        client,
        token,
        project_id,
        impact="VERY_HIGH",
        likelihood="HIGH",
        coordinating_units="Sở GDĐT; TVGS",
    )

    # Assert
    assert body["impact"] == "VERY_HIGH"
    assert body["likelihood"] == "HIGH"
    assert body["coordinating_units"] == "Sở GDĐT; TVGS"


async def test_risk_rejects_unknown_impact_level(
    client: httpx.AsyncClient, make_user: UserFactory
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/risk-issues",
        json={
            "record_type": "RISK",
            "title": "x",
            "description": "y",
            "impact": "CỰC CAO",
        },
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 422


async def test_schedule_matrix_returns_milestones_with_tracking_fields(
    client: httpx.AsyncClient, make_user: UserFactory
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    await _create_milestone(client, token, project_id, code="M1", pm_comment="ghi chú")
    await _create_milestone(client, token, project_id, code="M2", name="Nghiệm thu")

    # Act
    response = await client.get(
        f"/api/v1/projects/{project_id}/schedule-matrix", headers=_bearer(token)
    )

    # Assert
    assert response.status_code == 200, response.text
    body = response.json()
    assert [row["code"] for row in body["rows"]] == ["M1", "M2"]
    assert body["rows"][0]["pm_comment"] == "ghi chú"
    assert body["total"] == 2


async def test_risk_matrix_orders_risks_by_score_descending(
    client: httpx.AsyncClient, make_user: UserFactory
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    await _create_risk(client, token, project_id, title="Thấp", impact="LOW", likelihood="LOW")
    await _create_risk(
        client, token, project_id, title="Cao", impact="VERY_HIGH", likelihood="HIGH"
    )

    # Act
    response = await client.get(
        f"/api/v1/projects/{project_id}/risk-matrix", headers=_bearer(token)
    )

    # Assert
    assert response.status_code == 200, response.text
    rows = response.json()["rows"]
    assert [row["title"] for row in rows] == ["Cao", "Thấp"]
    assert rows[0]["score"] == 12
    assert rows[1]["score"] == 1
