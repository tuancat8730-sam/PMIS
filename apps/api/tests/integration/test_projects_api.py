import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role
from app.models.audit_log import AuditLog
from tests.integration.helpers import PROJECT_PAYLOAD, UserFactory, login_as

pytestmark = pytest.mark.integration


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _pm_token(client: httpx.AsyncClient, make_user: UserFactory) -> str:
    await make_user(email="pm@example.com", role=Role.PM)
    return await login_as(client, "pm@example.com")


async def test_pm_creates_project_with_on_track_health(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token = await _pm_token(client, make_user)

    # Act
    response = await client.post("/api/v1/projects", json=PROJECT_PAYLOAD, headers=_bearer(token))

    # Assert
    body = response.json()
    assert response.status_code == 201
    assert body["code"] == "SGD-HCM-CSVC-2026"
    assert body["archetype"] == "IT_SYSTEM"
    assert body["health_status"] == "ON_TRACK"
    assert body["total_investment"] == "5999498939.00"


async def test_duplicate_project_code_returns_409(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token = await _pm_token(client, make_user)
    await client.post("/api/v1/projects", json=PROJECT_PAYLOAD, headers=_bearer(token))

    # Act
    response = await client.post("/api/v1/projects", json=PROJECT_PAYLOAD, headers=_bearer(token))

    # Assert
    assert response.status_code == 409


async def test_project_creation_is_audited_with_actor(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    pm = await make_user(email="pm@example.com", role=Role.PM)
    token = await login_as(client, "pm@example.com")

    # Act
    await client.post("/api/v1/projects", json=PROJECT_PAYLOAD, headers=_bearer(token))

    # Assert
    audited = (
        await session.execute(select(AuditLog).where(AuditLog.action == "project.create"))
    ).scalar_one()
    assert audited.actor_id == pm.id
    assert audited.entity_type == "project"
    assert audited.changes == {"code": "SGD-HCM-CSVC-2026", "archetype": "IT_SYSTEM"}


async def test_consultant_cannot_create_project(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    await make_user(email="consultant@example.com", role=Role.PM_CONSULTANT)
    token = await login_as(client, "consultant@example.com")

    # Act
    response = await client.post("/api/v1/projects", json=PROJECT_PAYLOAD, headers=_bearer(token))

    # Assert
    assert response.status_code == 403


async def test_end_date_before_start_date_returns_422(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token = await _pm_token(client, make_user)
    payload = {**PROJECT_PAYLOAD, "start_date": "2026-12-31", "end_date": "2026-01-15"}

    # Act
    response = await client.post("/api/v1/projects", json=payload, headers=_bearer(token))

    # Assert
    assert response.status_code == 422


async def test_non_positive_investment_returns_422(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token = await _pm_token(client, make_user)
    payload = {**PROJECT_PAYLOAD, "total_investment": "0"}

    # Act
    response = await client.post("/api/v1/projects", json=payload, headers=_bearer(token))

    # Assert
    assert response.status_code == 422


async def test_unknown_archetype_returns_422(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token = await _pm_token(client, make_user)
    payload = {**PROJECT_PAYLOAD, "archetype": "KHONG_TON_TAI"}

    # Act
    response = await client.post("/api/v1/projects", json=payload, headers=_bearer(token))

    # Assert
    assert response.status_code == 422


async def test_list_returns_created_projects(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token = await _pm_token(client, make_user)
    await client.post("/api/v1/projects", json=PROJECT_PAYLOAD, headers=_bearer(token))

    # Act
    response = await client.get("/api/v1/projects", headers=_bearer(token))

    # Assert
    assert response.status_code == 200
    assert [item["code"] for item in response.json()] == ["SGD-HCM-CSVC-2026"]


async def test_get_project_by_id_returns_it(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token = await _pm_token(client, make_user)
    created = await client.post("/api/v1/projects", json=PROJECT_PAYLOAD, headers=_bearer(token))

    # Act
    response = await client.get(f"/api/v1/projects/{created.json()['id']}", headers=_bearer(token))

    # Assert
    assert response.status_code == 200
    assert response.json()["short_name"] == "SGD-HCM CSVC 2026"


async def test_unknown_project_returns_404(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token = await _pm_token(client, make_user)

    # Act
    response = await client.get(
        "/api/v1/projects/00000000-0000-0000-0000-000000000000",
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 404


async def test_anonymous_cannot_list_projects(client: httpx.AsyncClient) -> None:
    # Act
    response = await client.get("/api/v1/projects")

    # Assert
    assert response.status_code == 401
