import pytest
from fastapi import FastAPI

from app.cli import create_admin_account
from app.core.rbac import Role
from app.core.security import verify_password
from app.services.users import DuplicateEmailError

pytestmark = pytest.mark.integration

ADMIN_PASSWORD = "mat-khau-admin-dau-tien-2026"


async def test_create_admin_account_makes_active_admin_with_hashed_password(app: FastAPI) -> None:
    # Act
    user = await create_admin_account(
        app.state.session_factory,
        email="Chu-Tich@Example.com",
        full_name="Quản trị viên",
        password=ADMIN_PASSWORD,
    )

    # Assert
    assert user.email == "chu-tich@example.com"
    assert user.role == Role.ADMIN
    assert user.is_active is True
    assert user.hashed_password != ADMIN_PASSWORD
    assert verify_password(ADMIN_PASSWORD, user.hashed_password)


async def test_create_admin_account_rejects_existing_email(app: FastAPI) -> None:
    # Arrange
    await create_admin_account(
        app.state.session_factory,
        email="admin@example.com",
        full_name="Quản trị viên",
        password=ADMIN_PASSWORD,
    )

    # Act / Assert
    with pytest.raises(DuplicateEmailError):
        await create_admin_account(
            app.state.session_factory,
            email="admin@example.com",
            full_name="Quản trị viên",
            password=ADMIN_PASSWORD,
        )
