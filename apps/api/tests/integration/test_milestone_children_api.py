import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role
from app.models.audit_log import AuditLog
from tests.integration.helpers import UserFactory, create_project, login_as

pytestmark = pytest.mark.integration

FAR_FUTURE_END = "2099-12-31"
PAST_DUE_DATE = "2000-01-10"
TASKS_PATH = "/api/v1/projects/{project_id}/milestones/{milestone_id}/tasks"
NOTES_PATH = "/api/v1/projects/{project_id}/milestones/{milestone_id}/notes"


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _pm_with_milestone(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> tuple[str, str, str]:
    """Trả về (token PM, project_id, milestone_id) để các test gắn task và ghi chú vào."""
    await make_user(email="pm@example.com", role=Role.PM)
    pm_token = await login_as(client, "pm@example.com")
    project_id = await create_project(client, pm_token)
    response = await client.post(
        f"/api/v1/projects/{project_id}/milestones",
        json={"code": "M1", "name": "Khảo sát", "baseline_end": FAR_FUTURE_END},
        headers=_bearer(pm_token),
    )
    assert response.status_code == 201, response.text
    return pm_token, project_id, response.json()["id"]


async def _add_member(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    pm_token: str,
    project_id: str,
    email: str,
    role: Role,
) -> str:
    user = await make_user(email=email, role=role)
    response = await client.post(
        f"/api/v1/projects/{project_id}/members",
        json={"user_id": str(user.id), "role": role.value},
        headers=_bearer(pm_token),
    )
    assert response.status_code == 201, response.text
    return await login_as(client, email)


async def _create_task(
    client: httpx.AsyncClient,
    token: str,
    project_id: str,
    milestone_id: str,
    **overrides: object,
) -> dict[str, object]:
    response = await client.post(
        TASKS_PATH.format(project_id=project_id, milestone_id=milestone_id),
        json={"name": "Đo đạc hiện trạng", **overrides},
        headers=_bearer(token),
    )
    assert response.status_code == 201, response.text
    body: dict[str, object] = response.json()
    return body


async def test_pm_creates_task_with_default_not_started_status(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    pm_token, project_id, milestone_id = await _pm_with_milestone(client, make_user)

    # Act
    response = await client.post(
        TASKS_PATH.format(project_id=project_id, milestone_id=milestone_id),
        json={
            "name": "Đo đạc hiện trạng",
            "assignee": "Nguyễn Văn A",
            "due_date": FAR_FUTURE_END,
            "note": "Cần xe đo",
        },
        headers=_bearer(pm_token),
    )

    # Assert
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "NOT_STARTED"
    assert body["assignee"] == "Nguyễn Văn A"
    assert body["due_date"] == FAR_FUTURE_END
    assert body["note"] == "Cần xe đo"
    assert body["is_overdue"] is False


async def test_supervision_consultant_updates_and_deletes_task(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    pm_token, project_id, milestone_id = await _pm_with_milestone(client, make_user)
    tvgs_token = await _add_member(
        client, make_user, pm_token, project_id, "tvgs@example.com", Role.SUPERVISION_CONSULTANT
    )
    task = await _create_task(client, pm_token, project_id, milestone_id)
    task_url = f"{TASKS_PATH.format(project_id=project_id, milestone_id=milestone_id)}/{task['id']}"

    # Act
    patch_response = await client.patch(
        task_url, json={"status": "COMPLETED"}, headers=_bearer(tvgs_token)
    )
    delete_response = await client.delete(task_url, headers=_bearer(tvgs_token))

    # Assert
    assert patch_response.status_code == 200, patch_response.text
    assert patch_response.json()["status"] == "COMPLETED"
    assert delete_response.status_code == 204


async def test_investor_cannot_create_task(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    pm_token, project_id, milestone_id = await _pm_with_milestone(client, make_user)
    investor_token = await _add_member(
        client, make_user, pm_token, project_id, "investor@example.com", Role.INVESTOR
    )

    # Act
    response = await client.post(
        TASKS_PATH.format(project_id=project_id, milestone_id=milestone_id),
        json={"name": "Không được phép"},
        headers=_bearer(investor_token),
    )

    # Assert
    assert response.status_code == 403


async def test_update_task_through_unknown_milestone_returns_404(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    pm_token, project_id, milestone_id = await _pm_with_milestone(client, make_user)
    task = await _create_task(client, pm_token, project_id, milestone_id)
    other_milestone_id = "00000000-0000-0000-0000-000000000001"

    # Act
    response = await client.patch(
        f"{TASKS_PATH.format(project_id=project_id, milestone_id=other_milestone_id)}/{task['id']}",
        json={"status": "COMPLETED"},
        headers=_bearer(pm_token),
    )

    # Assert
    assert response.status_code == 404


async def test_open_task_past_due_date_is_marked_overdue(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    pm_token, project_id, milestone_id = await _pm_with_milestone(client, make_user)

    # Act
    task = await _create_task(client, pm_token, project_id, milestone_id, due_date=PAST_DUE_DATE)

    # Assert
    assert task["is_overdue"] is True


async def test_completed_task_past_due_date_is_not_marked_overdue(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    pm_token, project_id, milestone_id = await _pm_with_milestone(client, make_user)

    # Act
    task = await _create_task(
        client,
        pm_token,
        project_id,
        milestone_id,
        due_date=PAST_DUE_DATE,
        status="COMPLETED",
    )

    # Assert
    assert task["is_overdue"] is False


async def test_task_mutations_write_audit_rows(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    pm_token, project_id, milestone_id = await _pm_with_milestone(client, make_user)
    task = await _create_task(client, pm_token, project_id, milestone_id)
    task_url = f"{TASKS_PATH.format(project_id=project_id, milestone_id=milestone_id)}/{task['id']}"

    # Act
    await client.patch(task_url, json={"status": "IN_PROGRESS"}, headers=_bearer(pm_token))
    await client.delete(task_url, headers=_bearer(pm_token))

    # Assert
    rows = await session.execute(
        select(AuditLog.action).where(AuditLog.action.like("milestone_task.%"))
    )
    actions = sorted(rows.scalars().all())
    assert actions == ["milestone_task.create", "milestone_task.delete", "milestone_task.update"]


async def test_supervision_consultant_adds_note_and_notes_are_append_only(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    pm_token, project_id, milestone_id = await _pm_with_milestone(client, make_user)
    tvgs_token = await _add_member(
        client, make_user, pm_token, project_id, "tvgs@example.com", Role.SUPERVISION_CONSULTANT
    )
    notes_url = NOTES_PATH.format(project_id=project_id, milestone_id=milestone_id)

    # Act
    create_response = await client.post(
        notes_url, json={"body": "Đã khảo sát trường A"}, headers=_bearer(tvgs_token)
    )
    patch_response = await client.patch(
        notes_url, json={"body": "Sửa"}, headers=_bearer(tvgs_token)
    )
    delete_response = await client.delete(notes_url, headers=_bearer(tvgs_token))

    # Assert
    assert create_response.status_code == 201, create_response.text
    assert create_response.json()["body"] == "Đã khảo sát trường A"
    assert create_response.json()["created_by"] is not None
    assert patch_response.status_code == 405
    assert delete_response.status_code == 405


async def test_investor_cannot_add_note(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    pm_token, project_id, milestone_id = await _pm_with_milestone(client, make_user)
    investor_token = await _add_member(
        client, make_user, pm_token, project_id, "investor@example.com", Role.INVESTOR
    )

    # Act
    response = await client.post(
        NOTES_PATH.format(project_id=project_id, milestone_id=milestone_id),
        json={"body": "Không được phép"},
        headers=_bearer(investor_token),
    )

    # Assert
    assert response.status_code == 403


async def test_note_on_milestone_of_another_project_returns_404(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    pm_token, _project_id, milestone_id = await _pm_with_milestone(client, make_user)
    second_project_id = await create_project(client, pm_token, code="SGD-LD-2026")

    # Act
    response = await client.post(
        NOTES_PATH.format(project_id=second_project_id, milestone_id=milestone_id),
        json={"body": "Sai dự án"},
        headers=_bearer(pm_token),
    )

    # Assert
    assert response.status_code == 404
