from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.rbac import Role
from app.models.milestone import Milestone
from tests.integration.helpers import (
    CONTRACT_PAYLOAD,
    create_contract,
    create_project,
    login_as,
)

pytestmark = pytest.mark.integration

ENDPOINT = "/api/v1/command-center"


def _today() -> date:
    return datetime.now(UTC).date()


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _seed_open_milestone(session: AsyncSession, project_id: str, code: str) -> None:
    session.add(
        Milestone(
            project_id=project_id,
            code=code,
            name=f"Mốc {code}",
            baseline_end=_today() + timedelta(days=1),
            is_hard_deadline=False,
        )
    )
    await session.commit()


async def _create_pm_project(client: httpx.AsyncClient, make_user, code: str, email: str) -> str:
    await make_user(email=email, role=Role.PM)
    token = await login_as(client, email)
    return await create_project(client, token, code=code, short_name=code)


async def test_admin_kpi_sums_contracts_and_counts_red_milestones(
    client: httpx.AsyncClient,
    session: AsyncSession,
    make_user,
) -> None:
    # Arrange
    project_id = await _create_pm_project(client, make_user, "CC-A", "pm-a@example.com")
    pm_token = await login_as(client, "pm-a@example.com")
    await create_contract(client, pm_token, project_id)
    await _seed_open_milestone(session, project_id, "M1")
    await make_user(email="admin-cc@example.com", role=Role.ADMIN)
    admin_token = await login_as(client, "admin-cc@example.com")

    # Act
    response = await client.get(ENDPOINT, headers=_bearer(admin_token))

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert Decimal(body["kpi"]["contract_value_by_kind"]["MAIN"]) == Decimal(
        CONTRACT_PAYLOAD["contract_value"]
    )
    assert Decimal(body["kpi"]["contract_value_by_kind"]["CONSULTING"]) == Decimal("0")
    assert body["kpi"]["red_alert_count"] == 1
    assert body["kpi"]["pending_signature_count"] is None
    assert body["red_alerts"][0]["code"] == "M1"


async def test_member_sees_only_projects_they_belong_to(
    client: httpx.AsyncClient,
    make_user,
) -> None:
    # Arrange
    await _create_pm_project(client, make_user, "CC-B1", "pm-b1@example.com")
    await _create_pm_project(client, make_user, "CC-B2", "pm-b2@example.com")
    token = await login_as(client, "pm-b1@example.com")

    # Act
    response = await client.get(ENDPOINT, headers=_bearer(token))

    # Assert
    assert response.status_code == 200
    codes = [row["code"] for row in response.json()["projects"]]
    assert codes == ["CC-B1"]


async def test_query_count_does_not_grow_with_project_count(
    client: httpx.AsyncClient,
    engine: AsyncEngine,
    make_user,
) -> None:
    # Arrange
    await make_user(email="admin-n1@example.com", role=Role.ADMIN)
    token = await login_as(client, "admin-n1@example.com")
    await create_project(client, token, code="CC-N-1", short_name="CC-N-1")
    one_project = await _count_statements(client, engine, token)

    for index in range(2, 5):
        await create_project(client, token, code=f"CC-N-{index}", short_name=f"CC-N-{index}")
    four_projects = await _count_statements(client, engine, token)

    # Assert
    assert four_projects == one_project


async def _count_statements(client: httpx.AsyncClient, engine: AsyncEngine, token: str) -> int:
    statements: list[str] = []

    def _record(conn, cursor, statement, parameters, context, executemany) -> None:  # noqa: ANN001
        statements.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", _record)
    try:
        response = await client.get(ENDPOINT, headers=_bearer(token))
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", _record)
    assert response.status_code == 200
    return len(statements)


def test_endpoint_is_read_only(app) -> None:  # noqa: ANN001
    # Arrange: OpenAPI liệt kê đúng method của từng đường dẫn, kể cả router đã include.
    paths = app.openapi()["paths"]

    # Assert
    assert set(paths[ENDPOINT].keys()) == {"get"}


async def test_unauthenticated_request_is_rejected(client: httpx.AsyncClient) -> None:
    # Act
    response = await client.get(ENDPOINT)

    # Assert
    assert response.status_code == 401
