from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest

from app.core.config import Settings
from app.core.rbac import Role
from app.main import create_app
from tests.integration.helpers import UserFactory, login_as

pytestmark = pytest.mark.integration

WRONG_PASSWORD = "mat-khau-sai-khong-dung-2026"
NEW_USER_EMAIL_TEMPLATE = "nguoi-dung-{index}@example.com"
NEW_USER_PASSWORD = "mat-khau-moi-rat-manh-2026"


@asynccontextmanager
async def _limited_client(settings: Settings, **limits: int) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(settings.model_copy(update=limits))
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        await app.state.engine.dispose()


async def test_login_is_rejected_with_429_and_retry_after_after_too_many_attempts(
    settings: Settings,
) -> None:
    # Arrange
    async with _limited_client(
        settings,
        login_rate_limit_attempts=2,
        login_rate_limit_window_seconds=900,
    ) as client:
        credentials = {"username": "ai-do@example.com", "password": WRONG_PASSWORD}

        # Act
        first = await client.post("/api/v1/auth/login", data=credentials)
        second = await client.post("/api/v1/auth/login", data=credentials)
        blocked = await client.post("/api/v1/auth/login", data=credentials)

    # Assert
    assert first.status_code == 401
    assert second.status_code == 401
    assert blocked.status_code == 429
    assert blocked.json()["detail"] == "Bạn thao tác quá nhiều lần, vui lòng thử lại sau"
    assert 0 < int(blocked.headers["Retry-After"]) <= 900


async def test_user_creation_is_rejected_with_429_after_too_many_writes(
    settings: Settings,
    make_user: UserFactory,
) -> None:
    # Arrange
    await make_user(email="admin-gioi-han@example.com", role=Role.ADMIN)
    async with _limited_client(
        settings,
        login_rate_limit_attempts=10,
        write_rate_limit_attempts=2,
        write_rate_limit_window_seconds=60,
    ) as client:
        token = await login_as(client, "admin-gioi-han@example.com")
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        responses = [
            await client.post(
                "/api/v1/users",
                json={
                    "email": NEW_USER_EMAIL_TEMPLATE.format(index=index),
                    "full_name": "Người dùng giới hạn",
                    "password": NEW_USER_PASSWORD,
                    "role": "FIELD_ENGINEER",
                },
                headers=headers,
            )
            for index in range(3)
        ]

    # Assert
    assert [response.status_code for response in responses] == [201, 201, 429]
    assert int(responses[-1].headers["Retry-After"]) > 0
