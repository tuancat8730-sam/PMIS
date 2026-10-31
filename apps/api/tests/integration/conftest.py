import asyncio
import os
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
from alembic import command
from alembic.config import Config
from cryptography.fernet import Fernet
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.core.config import Settings
from app.core.rbac import Role
from app.main import create_app
from app.models.user import User
from app.services.users import create_user
from tests.integration.helpers import TEST_PASSWORD, UserFactory

API_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Đặt TEST_DATABASE_URL để chạy integration test")
    database_name = make_url(url).database or ""
    if not database_name.endswith("_test"):
        # Test sẽ xóa toàn bộ schema public, nên từ chối chạy trên database không phải test.
        raise RuntimeError("TEST_DATABASE_URL phải trỏ tới database có hậu tố _test")
    return url


@pytest.fixture(scope="session")
def migrated_database(database_url: str) -> str:
    """Dựng lại schema từ migration Alembic để kiểm tra migration chạy được thật."""

    async def _drop_schema() -> None:
        engine = create_async_engine(database_url)
        async with engine.begin() as connection:
            await connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            await connection.execute(text("CREATE SCHEMA public"))
        await engine.dispose()

    asyncio.run(_drop_schema())
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "migrations"))
    config.attributes["database_url"] = database_url
    command.upgrade(config, "head")
    return database_url


@pytest.fixture(scope="session")
def settings(migrated_database: str) -> Settings:
    # Ngưỡng cao để các test không ảnh hưởng nhau; test rate limit tự dựng app với ngưỡng thấp.
    return Settings(
        database_url=migrated_database,
        jwt_secret="t" * 32,
        cccd_encryption_key=Fernet.generate_key().decode(),
        login_rate_limit_attempts=100_000,
        write_rate_limit_attempts=100_000,
    )


@pytest.fixture(scope="session")
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture(scope="session")
def engine(app: FastAPI) -> AsyncEngine:
    return app.state.engine


@pytest.fixture(autouse=True)
async def clean_tables(engine: AsyncEngine) -> AsyncIterator[None]:
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "TRUNCATE audit_logs, users, projects, project_members, project_stakeholders, "
                "contracts, contract_personnel, beneficiary_units CASCADE"
            )
        )
    yield


@pytest.fixture
async def session(app: FastAPI) -> AsyncIterator[AsyncSession]:
    async with app.state.session_factory() as db_session:
        yield db_session


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


@pytest.fixture
def make_user(session: AsyncSession) -> UserFactory:
    async def _make(
        *,
        email: str,
        role: Role,
        password: str = TEST_PASSWORD,
        is_active: bool = True,
    ) -> User:
        user = await create_user(
            session,
            email=email,
            full_name="Người dùng thử nghiệm",
            password=password,
            role=role,
        )
        user.is_active = is_active
        await session.commit()
        return user

    return _make
