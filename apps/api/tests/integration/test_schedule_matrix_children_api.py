import httpx
import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.rbac import Role
from tests.integration.helpers import UserFactory
from tests.integration.test_milestone_children_api import (
    _add_member,
    _bearer,
    _create_task,
    _pm_with_milestone,
)

pytestmark = pytest.mark.integration

PAST_DUE_DATE = "2000-01-10"
MATRIX_PATH = "/api/v1/projects/{project_id}/schedule-matrix"
MILESTONES_PATH = "/api/v1/projects/{project_id}/milestones"
NOTES_PATH = "/api/v1/projects/{project_id}/milestones/{milestone_id}/notes"


async def _matrix_row(
    client: httpx.AsyncClient,
    token: str,
    project_id: str,
    milestone_id: str,
) -> dict[str, object]:
    response = await client.get(MATRIX_PATH.format(project_id=project_id), headers=_bearer(token))
    assert response.status_code == 200, response.text
    rows: list[dict[str, object]] = response.json()["rows"]
    return next(row for row in rows if row["id"] == milestone_id)


async def _count_matrix_statements(
    client: httpx.AsyncClient,
    engine: AsyncEngine,
    token: str,
    project_id: str,
) -> int:
    statements: list[str] = []

    def _record(conn: object, cursor: object, statement: str, *args: object) -> None:
        statements.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", _record)
    try:
        response = await client.get(
            MATRIX_PATH.format(project_id=project_id), headers=_bearer(token)
        )
        assert response.status_code == 200, response.text
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", _record)
    return len(statements)


async def test_schedule_matrix_row_carries_tasks_and_notes_newest_first(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    pm_token, project_id, milestone_id = await _pm_with_milestone(client, make_user)
    tvgs_token = await _add_member(
        client, make_user, pm_token, project_id, "tvgs@example.com", Role.SUPERVISION_CONSULTANT
    )
    await _create_task(
        client, pm_token, project_id, milestone_id, name="Khảo sát", status="COMPLETED"
    )
    await _create_task(
        client, pm_token, project_id, milestone_id, name="Lập báo cáo", due_date=PAST_DUE_DATE
    )
    notes_url = NOTES_PATH.format(project_id=project_id, milestone_id=milestone_id)
    await client.post(notes_url, json={"body": "Ghi chú cũ"}, headers=_bearer(tvgs_token))
    await client.post(notes_url, json={"body": "Ghi chú mới"}, headers=_bearer(pm_token))

    # Act
    row = await _matrix_row(client, pm_token, project_id, milestone_id)

    # Assert
    tasks: list[dict[str, object]] = row["tasks"]  # type: ignore[assignment]
    notes: list[dict[str, object]] = row["notes"]  # type: ignore[assignment]
    assert [task["name"] for task in tasks] == ["Khảo sát", "Lập báo cáo"]
    assert tasks[1]["is_overdue"] is True
    assert [note["body"] for note in notes] == ["Ghi chú mới", "Ghi chú cũ"]


async def test_schedule_matrix_query_count_does_not_grow_with_milestones(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    engine: AsyncEngine,
) -> None:
    # Arrange
    pm_token, project_id, milestone_id = await _pm_with_milestone(client, make_user)
    await _create_task(client, pm_token, project_id, milestone_id)
    single_count = await _count_matrix_statements(client, engine, pm_token, project_id)
    for code in ("M2", "M3", "M4"):
        response = await client.post(
            MILESTONES_PATH.format(project_id=project_id),
            json={"code": code, "name": f"Mốc {code}", "baseline_end": "2099-12-31"},
            headers=_bearer(pm_token),
        )
        assert response.status_code == 201, response.text
        await _create_task(client, pm_token, project_id, response.json()["id"])

    # Act
    many_count = await _count_matrix_statements(client, engine, pm_token, project_id)

    # Assert
    assert many_count == single_count
