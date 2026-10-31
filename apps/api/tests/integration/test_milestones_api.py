import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role
from app.models.audit_log import AuditLog
from app.models.milestone_adjustment import MilestoneAdjustment
from tests.integration.helpers import (
    UserFactory,
    create_project,
    login_as,
)

pytestmark = pytest.mark.integration

PAST_BASELINE_END = "2000-01-10"
FAR_FUTURE_END = "2099-12-31"


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _milestone_payload(**overrides: object) -> dict[str, object]:
    return {
        "code": "M8",
        "name": "Nghiệm thu, bàn giao",
        "baseline_end": FAR_FUTURE_END,
        "is_hard_deadline": True,
        **overrides,
    }


async def _pm_with_project(client: httpx.AsyncClient, make_user: UserFactory) -> tuple[str, str]:
    await make_user(email="pm@example.com", role=Role.PM)
    token = await login_as(client, "pm@example.com")
    project_id = await create_project(client, token)
    return token, project_id


async def _create_milestone(
    client: httpx.AsyncClient,
    token: str,
    project_id: str,
    **overrides: object,
) -> dict[str, object]:
    response = await client.post(
        f"/api/v1/projects/{project_id}/milestones",
        json=_milestone_payload(**overrides),
        headers=_bearer(token),
    )
    assert response.status_code == 201, response.text
    body: dict[str, object] = response.json()
    return body


async def test_pm_creates_milestone_with_derived_overdue_status(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/milestones",
        json=_milestone_payload(code="M1", baseline_end=PAST_BASELINE_END, is_hard_deadline=False),
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["display_status"] == "OVERDUE"
    assert body["slippage_days"] > 0
    assert body["status"] == "NOT_STARTED"


async def test_hard_deadline_milestone_rejects_adjusted_end_after_baseline(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/milestones",
        json=_milestone_payload(
            baseline_end="2026-11-30",
            adjusted_end="2026-12-02",
            is_hard_deadline=True,
        ),
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 422
    assert "mốc cứng" in response.json()["detail"].lower()


async def test_duplicate_milestone_code_returns_409(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    await _create_milestone(client, token, project_id, code="M2")

    # Act
    response = await client.post(
        f"/api/v1/projects/{project_id}/milestones",
        json=_milestone_payload(code="M2"),
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 409


async def test_investor_can_read_milestones_but_cannot_create_one(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    pm_token, project_id = await _pm_with_project(client, make_user)
    await _create_milestone(client, pm_token, project_id)
    investor = await make_user(email="investor@example.com", role=Role.INVESTOR)
    await client.post(
        f"/api/v1/projects/{project_id}/members",
        json={"user_id": str(investor.id), "role": Role.INVESTOR.value},
        headers=_bearer(pm_token),
    )
    investor_token = await login_as(client, "investor@example.com")

    # Act
    read_response = await client.get(
        f"/api/v1/projects/{project_id}/milestones", headers=_bearer(investor_token)
    )
    write_response = await client.post(
        f"/api/v1/projects/{project_id}/milestones",
        json=_milestone_payload(code="M9"),
        headers=_bearer(investor_token),
    )

    # Assert
    assert read_response.status_code == 200
    assert len(read_response.json()) == 1
    assert write_response.status_code == 403


async def test_completing_milestone_with_unconfirmed_hold_point_is_rejected(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    milestone = await _create_milestone(client, token, project_id, code="M3")
    await client.post(
        f"/api/v1/projects/{project_id}/hold-points",
        json={"code": "H3", "name": "Điểm dừng H3", "milestone_id": milestone["id"]},
        headers=_bearer(token),
    )

    # Act
    response = await client.patch(
        f"/api/v1/projects/{project_id}/milestones/{milestone['id']}",
        json={"status": "COMPLETED"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 422
    assert "H3" in response.json()["detail"]


async def test_changing_completed_milestone_without_reason_is_rejected(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    milestone = await _create_milestone(
        client, token, project_id, code="M4", baseline_end=FAR_FUTURE_END, is_hard_deadline=False
    )
    await client.patch(
        f"/api/v1/projects/{project_id}/milestones/{milestone['id']}",
        json={"status": "COMPLETED", "actual_end": "2026-10-01"},
        headers=_bearer(token),
    )

    # Act
    response = await client.patch(
        f"/api/v1/projects/{project_id}/milestones/{milestone['id']}",
        json={"adjusted_end": "2099-06-30"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 422
    assert "lý do" in response.json()["detail"].lower()


async def test_changing_completed_milestone_with_reason_records_adjustment(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    milestone = await _create_milestone(
        client, token, project_id, code="M5", baseline_end=FAR_FUTURE_END, is_hard_deadline=False
    )
    await client.patch(
        f"/api/v1/projects/{project_id}/milestones/{milestone['id']}",
        json={"status": "COMPLETED", "actual_end": "2026-10-01"},
        headers=_bearer(token),
    )

    # Act
    response = await client.patch(
        f"/api/v1/projects/{project_id}/milestones/{milestone['id']}",
        json={"adjusted_end": "2099-06-30", "reason": "Chủ đầu tư yêu cầu lùi hạn có văn bản"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 200, response.text
    adjustments = (await session.execute(select(MilestoneAdjustment))).scalars().all()
    assert len(adjustments) == 1
    assert adjustments[0].reason == "Chủ đầu tư yêu cầu lùi hạn có văn bản"
    audit_rows = (
        (
            await session.execute(
                select(AuditLog.action).where(AuditLog.action == "milestone.adjust")
            )
        )
        .scalars()
        .all()
    )
    assert audit_rows == ["milestone.adjust"]


async def test_creating_milestone_writes_audit_row(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)

    # Act
    await _create_milestone(client, token, project_id, code="M6")

    # Assert
    actions = (
        (
            await session.execute(
                select(AuditLog.action).where(AuditLog.action == "milestone.create")
            )
        )
        .scalars()
        .all()
    )
    assert actions == ["milestone.create"]
