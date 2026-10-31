from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

import httpx

from app.core.config import Settings
from app.main import create_app
from app.models.user import User

TEST_PASSWORD = "mat-khau-test-rat-manh-2026"
UserFactory = Callable[..., Awaitable[User]]

PROJECT_PAYLOAD: dict[str, Any] = {
    "code": "SGD-HCM-CSVC-2026",
    "name": "Đầu tư cơ sở vật chất trường học TP.HCM 2026",
    "short_name": "SGD-HCM CSVC 2026",
    "archetype": "IT_SYSTEM",
    "investor_name": "Sở GD&ĐT TP.HCM",
    "decision_authority": "UBND TP.HCM",
    "total_investment": "5999498939.00",
    "start_date": "2026-01-15",
    "end_date": "2026-12-31",
}

CONTRACT_PAYLOAD: dict[str, Any] = {
    "package_name": "Gói thầu chính: Thiết bị và phần mềm lớp 10",
    "contract_number": "29/HĐKT-DVN",
    "signed_date": "2026-02-01",
    "expiration_date": "2026-06-01",
    "contract_value": "4848186000.00",
}


@asynccontextmanager
async def limited_client(settings: Settings, **limits: int) -> AsyncIterator[httpx.AsyncClient]:
    """Client riêng với ngưỡng rate limit thấp; app được dựng mới nên không ảnh hưởng test khác."""
    app = create_app(settings.model_copy(update=limits))
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        await app.state.engine.dispose()


async def login_as(client: httpx.AsyncClient, email: str, password: str = TEST_PASSWORD) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


async def create_project(
    client: httpx.AsyncClient,
    token: str,
    **overrides: Any,
) -> str:
    """Tạo dự án mẫu qua API, trả về id để các test khác gắn dữ liệu vào."""
    response = await client.post(
        "/api/v1/projects",
        json={**PROJECT_PAYLOAD, **overrides},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, response.text
    project_id: str = response.json()["id"]
    return project_id


async def create_contract(client: httpx.AsyncClient, token: str, project_id: str) -> str:
    """Tạo hợp đồng mẫu thuộc dự án, trả về id để gắn nhân sự vào."""
    response = await client.post(
        f"/api/v1/projects/{project_id}/contracts",
        json=CONTRACT_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, response.text
    contract_id: str = response.json()["id"]
    return contract_id
