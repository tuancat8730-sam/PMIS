from collections.abc import Callable, Iterator
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.drive import get_drive_gateway
from app.core.rbac import Role
from app.integrations.drive import DriveApiError
from app.integrations.drive_gateway import DriveEntry
from app.models.audit_log import AuditLog
from tests.fakes.fake_drive_gateway import FakeDriveGateway
from tests.integration.helpers import UserFactory, create_project, login_as

pytestmark = pytest.mark.integration

ROOT = "root-folder-sgd"
PM_EMAIL = "pm-drive@example.com"
OUTSIDER_EMAIL = "outsider-drive@example.com"


class _FailingGateway:
    def list_children(self, folder_id: str) -> list[DriveEntry]:
        raise DriveApiError(403, "Drive trả lỗi 403 khi đọc thư mục")


def _file_entry(file_id: str, name: str) -> DriveEntry:
    return DriveEntry(
        drive_file_id=file_id,
        parent_id=ROOT,
        name=name,
        mime_type="application/pdf",
        size=512,
        web_view_link=f"https://drive.example/{file_id}",
        modified_time="2026-10-01T00:00:00Z",
        is_folder=False,
    )


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _sync_url(project_id: str) -> str:
    return f"/api/v1/projects/{project_id}/drive/sync"


def _files_url(project_id: str) -> str:
    return f"/api/v1/projects/{project_id}/drive/files"


@pytest.fixture
def override_gateway(app: FastAPI) -> Iterator[Callable[[Any], None]]:
    def _set(gateway: Any) -> None:
        app.dependency_overrides[get_drive_gateway] = lambda: gateway

    yield _set
    app.dependency_overrides.pop(get_drive_gateway, None)


async def test_pm_sync_stores_files_returns_counts_and_writes_audit(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
    override_gateway: Callable[[Any], None],
) -> None:
    # Arrange
    await make_user(email=PM_EMAIL, role=Role.PM)
    token = await login_as(client, PM_EMAIL)
    project_id = await create_project(client, token, drive_root_folder_id=ROOT)
    override_gateway(FakeDriveGateway({ROOT: [_file_entry("a", "tong_hop.pdf")]}))

    # Act
    sync = await client.post(_sync_url(project_id), headers=_bearer(token))
    files = await client.get(_files_url(project_id), headers=_bearer(token))

    # Assert
    assert sync.status_code == 200, sync.text
    assert sync.json() == {"scanned": 1, "created": 1, "updated": 0}
    assert [item["file_name"] for item in files.json()] == ["tong_hop.pdf"]
    audit = await session.execute(select(AuditLog).where(AuditLog.action == "drive.sync"))
    assert len(audit.scalars().all()) == 1


async def test_sync_of_project_without_root_folder_returns_409(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    override_gateway: Callable[[Any], None],
) -> None:
    # Arrange
    await make_user(email=PM_EMAIL, role=Role.PM)
    token = await login_as(client, PM_EMAIL)
    project_id = await create_project(client, token)
    override_gateway(FakeDriveGateway({}))

    # Act
    response = await client.post(_sync_url(project_id), headers=_bearer(token))

    # Assert
    assert response.status_code == 409


async def test_drive_failure_returns_502_and_stores_nothing(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    override_gateway: Callable[[Any], None],
) -> None:
    # Arrange
    await make_user(email=PM_EMAIL, role=Role.PM)
    token = await login_as(client, PM_EMAIL)
    project_id = await create_project(client, token, drive_root_folder_id=ROOT)
    override_gateway(_FailingGateway())

    # Act
    sync = await client.post(_sync_url(project_id), headers=_bearer(token))
    files = await client.get(_files_url(project_id), headers=_bearer(token))

    # Assert
    assert sync.status_code == 502
    assert files.json() == []


async def test_sync_without_configured_service_account_returns_503(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    await make_user(email=PM_EMAIL, role=Role.PM)
    token = await login_as(client, PM_EMAIL)
    project_id = await create_project(client, token, drive_root_folder_id=ROOT)

    # Act
    response = await client.post(_sync_url(project_id), headers=_bearer(token))

    # Assert
    assert response.status_code == 503


async def test_non_member_cannot_trigger_sync(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    override_gateway: Callable[[Any], None],
) -> None:
    # Arrange
    await make_user(email=PM_EMAIL, role=Role.PM)
    pm_token = await login_as(client, PM_EMAIL)
    project_id = await create_project(client, pm_token, drive_root_folder_id=ROOT)
    await make_user(email=OUTSIDER_EMAIL, role=Role.INVESTOR)
    outsider_token = await login_as(client, OUTSIDER_EMAIL)
    override_gateway(FakeDriveGateway({ROOT: []}))

    # Act
    response = await client.post(_sync_url(project_id), headers=_bearer(outsider_token))

    # Assert
    assert response.status_code == 403
