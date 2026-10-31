from datetime import timedelta
from uuid import uuid4

import httpx
import pytest
from fastapi import Depends, FastAPI

from app.core.config import Settings
from app.core.rbac import Principal, Role, get_current_principal, require_roles
from app.core.security import create_access_token

pytestmark = pytest.mark.unit

SECRET = "x" * 32


def _build_app() -> FastAPI:
    app = FastAPI()
    app.state.settings = Settings(
        database_url="postgresql+asyncpg://unused",
        jwt_secret=SECRET,
        cccd_encryption_key="unused",
    )

    @app.get("/admin-only")
    async def admin_only(
        principal: Principal = Depends(require_roles(Role.ADMIN)),
    ) -> dict[str, str]:
        return {"user_id": str(principal.user_id), "role": principal.role}

    @app.get("/me")
    async def me(principal: Principal = Depends(get_current_principal)) -> dict[str, str]:
        return {"role": principal.role}

    return app


def _token(role: str, user_id: str | None = None) -> str:
    return create_access_token(
        subject=user_id or str(uuid4()),
        role=role,
        secret=SECRET,
        algorithm="HS256",
        expires_in=timedelta(minutes=5),
    )


async def _get(path: str, token: str | None = None) -> httpx.Response:
    transport = httpx.ASGITransport(app=_build_app())
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path, headers=headers)


async def test_missing_token_returns_401() -> None:
    # Act
    response = await _get("/me")

    # Assert
    assert response.status_code == 401


async def test_invalid_token_returns_401() -> None:
    # Act
    response = await _get("/me", token="khong.phai.jwt")

    # Assert
    assert response.status_code == 401


async def test_token_with_unknown_role_returns_401() -> None:
    # Arrange
    token = _token(role="SIEU_QUAN_TRI")

    # Act
    response = await _get("/me", token=token)

    # Assert
    assert response.status_code == 401


async def test_wrong_role_returns_403() -> None:
    # Arrange
    token = _token(role=Role.FIELD_ENGINEER)

    # Act
    response = await _get("/admin-only", token=token)

    # Assert
    assert response.status_code == 403


async def test_allowed_role_passes_and_exposes_principal() -> None:
    # Arrange
    user_id = str(uuid4())
    token = _token(role=Role.ADMIN, user_id=user_id)

    # Act
    response = await _get("/admin-only", token=token)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"user_id": user_id, "role": "ADMIN"}
