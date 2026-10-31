import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role
from app.core.security import verify_password
from app.models.audit_log import AuditLog
from app.models.user import User
from tests.integration.helpers import UserFactory, login_as

pytestmark = pytest.mark.integration

NEW_USER_PAYLOAD = {
    "email": "Engineer@Example.com",
    "full_name": "Kỹ sư hiện trường",
    "password": "mat-khau-moi-rat-manh-2026",
    "role": "FIELD_ENGINEER",
}


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_admin_creates_user_and_response_hides_password(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    await make_user(email="admin@example.com", role=Role.ADMIN)
    token = await login_as(client, "admin@example.com")

    # Act
    response = await client.post("/api/v1/users", json=NEW_USER_PAYLOAD, headers=_bearer(token))

    # Assert
    body = response.json()
    assert response.status_code == 201
    assert body["email"] == "engineer@example.com"
    assert body["role"] == "FIELD_ENGINEER"
    assert "password" not in body
    assert "hashed_password" not in body


async def test_created_user_password_is_stored_as_hash(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    await make_user(email="admin@example.com", role=Role.ADMIN)
    token = await login_as(client, "admin@example.com")

    # Act
    await client.post("/api/v1/users", json=NEW_USER_PAYLOAD, headers=_bearer(token))

    # Assert
    stored = (
        await session.execute(select(User).where(User.email == "engineer@example.com"))
    ).scalar_one()
    assert stored.hashed_password != NEW_USER_PAYLOAD["password"]
    assert verify_password(NEW_USER_PAYLOAD["password"], stored.hashed_password)


async def test_user_creation_is_audited_with_actor(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    admin = await make_user(email="admin@example.com", role=Role.ADMIN)
    token = await login_as(client, "admin@example.com")

    # Act
    await client.post("/api/v1/users", json=NEW_USER_PAYLOAD, headers=_bearer(token))

    # Assert
    created = (
        await session.execute(select(AuditLog).where(AuditLog.action == "user.create"))
    ).scalar_one()
    assert created.actor_id == admin.id
    assert created.changes == {"email": "engineer@example.com", "role": "FIELD_ENGINEER"}


async def test_duplicate_email_returns_409(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    await make_user(email="admin@example.com", role=Role.ADMIN)
    await make_user(email="engineer@example.com", role=Role.FIELD_ENGINEER)
    token = await login_as(client, "admin@example.com")

    # Act
    response = await client.post("/api/v1/users", json=NEW_USER_PAYLOAD, headers=_bearer(token))

    # Assert
    assert response.status_code == 409


async def test_non_admin_cannot_create_user(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    await make_user(email="pm@example.com", role=Role.PM)
    token = await login_as(client, "pm@example.com")

    # Act
    response = await client.post("/api/v1/users", json=NEW_USER_PAYLOAD, headers=_bearer(token))

    # Assert
    assert response.status_code == 403


async def test_short_password_is_rejected_with_422(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    await make_user(email="admin@example.com", role=Role.ADMIN)
    token = await login_as(client, "admin@example.com")

    # Act
    response = await client.post(
        "/api/v1/users",
        json={**NEW_USER_PAYLOAD, "password": "ngan"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 422
