from collections.abc import Awaitable, Callable

import httpx

from app.models.user import User

TEST_PASSWORD = "mat-khau-test-rat-manh-2026"
UserFactory = Callable[..., Awaitable[User]]


async def login_as(client: httpx.AsyncClient, email: str, password: str = TEST_PASSWORD) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]
