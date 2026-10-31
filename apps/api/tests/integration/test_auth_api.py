import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role
from app.models.audit_log import AuditLog
from tests.integration.helpers import TEST_PASSWORD, UserFactory, login_as

pytestmark = pytest.mark.integration

INVALID_CREDENTIALS = "Email hoặc mật khẩu không đúng"


async def _audit_actions(session: AsyncSession) -> list[str]:
    result = await session.execute(select(AuditLog.action).order_by(AuditLog.created_at))
    return list(result.scalars().all())


async def test_login_with_valid_credentials_returns_token_and_role(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    await make_user(email="pm@example.com", role=Role.PM)

    # Act
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "pm@example.com", "password": TEST_PASSWORD},
    )

    # Assert
    body = response.json()
    assert response.status_code == 200
    assert body["token_type"] == "bearer"
    assert body["role"] == "PM"
    assert body["access_token"]
    assert "hashed_password" not in body


async def test_successful_login_writes_audit_entry_for_actor(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    user = await make_user(email="pm@example.com", role=Role.PM)

    # Act
    await client.post(
        "/api/v1/auth/login",
        data={"username": "pm@example.com", "password": TEST_PASSWORD},
    )

    # Assert
    entries = (await session.execute(select(AuditLog))).scalars().all()
    assert [(entry.action, entry.actor_id) for entry in entries] == [("auth.login", user.id)]


async def test_wrong_password_returns_401_and_audits_failure(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    await make_user(email="pm@example.com", role=Role.PM)

    # Act
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "pm@example.com", "password": "sai-mat-khau-hoan-toan"},
    )

    # Assert
    assert response.status_code == 401
    assert response.json()["detail"] == INVALID_CREDENTIALS
    assert await _audit_actions(session) == ["auth.login_failed"]


async def test_unknown_email_returns_same_401_message(client: httpx.AsyncClient) -> None:
    # Act
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "khong-ton-tai@example.com", "password": TEST_PASSWORD},
    )

    # Assert
    assert response.status_code == 401
    assert response.json()["detail"] == INVALID_CREDENTIALS


async def test_inactive_user_cannot_log_in(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    await make_user(email="nghi-viec@example.com", role=Role.PM, is_active=False)

    # Act
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "nghi-viec@example.com", "password": TEST_PASSWORD},
    )

    # Assert
    assert response.status_code == 401


async def test_me_returns_current_user_without_password_hash(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    await make_user(email="pm@example.com", role=Role.PM)
    token = await login_as(client, "pm@example.com")

    # Act
    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    # Assert
    body = response.json()
    assert response.status_code == 200
    assert body["email"] == "pm@example.com"
    assert body["role"] == "PM"
    assert "hashed_password" not in body


async def test_me_without_token_returns_401(client: httpx.AsyncClient) -> None:
    # Act
    response = await client.get("/api/v1/auth/me")

    # Assert
    assert response.status_code == 401


async def test_me_rejects_token_of_user_deactivated_after_login(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    user = await make_user(email="pm@example.com", role=Role.PM)
    token = await login_as(client, "pm@example.com")
    user.is_active = False
    await session.commit()

    # Act
    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    # Assert
    assert response.status_code == 401
