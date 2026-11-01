from collections.abc import Callable, Iterator
from typing import Any

import httpx
import pytest
from app.api.v1.drive_uploads import get_drive_writer
from fastapi import FastAPI

from app.core.rbac import Role
from app.integrations.drive_gateway import DriveEntry
from tests.fakes.fake_drive_writer import FakeDriveWriter
from tests.integration.helpers import UserFactory, create_project, login_as

pytestmark = pytest.mark.integration

PM_EMAIL = "pm-upload@example.com"
ROOT = "root-upload"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
FOLDER_MIME = "application/vnd.google-apps.folder"
WEEKLY_FOLDER_ID = "f-bao-cao-pmis"


def _folder(folder_id: str, name: str, parent: str) -> DriveEntry:
    return DriveEntry(
        drive_file_id=folder_id,
        parent_id=parent,
        name=name,
        mime_type=FOLDER_MIME,
        size=None,
        web_view_link=None,
        modified_time="2026-11-01T00:00:00Z",
        is_folder=True,
    )


def _writer_with_weekly_folder() -> FakeDriveWriter:
    return FakeDriveWriter(
        tree={ROOT: [_folder(WEEKLY_FOLDER_ID, "Báo cáo tuần (pmis)", ROOT)]},
    )


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _upload_url(project_id: str) -> str:
    return f"/api/v1/projects/{project_id}/drive/uploads"


@pytest.fixture
def override_writer(app: FastAPI) -> Iterator[Callable[[Any], None]]:
    def _set(writer: Any) -> None:
        app.dependency_overrides[get_drive_writer] = lambda: writer

    yield _set
    app.dependency_overrides.pop(get_drive_writer, None)


async def _pm_project(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    root: str | None,
) -> tuple[str, str]:
    await make_user(email=PM_EMAIL, role=Role.PM)
    token = await login_as(client, PM_EMAIL)
    project_id = await create_project(client, token, drive_root_folder_id=root)
    return token, project_id


async def test_pm_upload_lands_in_pmis_folder_and_second_push_updates(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    override_writer: Callable[[Any], None],
) -> None:
    # Arrange
    token, project_id = await _pm_project(client, make_user, ROOT)
    writer = _writer_with_weekly_folder()
    override_writer(writer)

    # Act
    first = await client.post(
        _upload_url(project_id),
        data={"kind": "WEEKLY_REPORT"},
        files={"file": ("bao_cao_tuan_01.docx", b"ban 1", DOCX_MIME)},
        headers=_bearer(token),
    )
    second = await client.post(
        _upload_url(project_id),
        data={"kind": "WEEKLY_REPORT"},
        files={"file": ("bao_cao_tuan_01.docx", b"ban 2", DOCX_MIME)},
        headers=_bearer(token),
    )

    # Assert
    assert first.status_code == 201, first.text
    assert first.json()["created"] is True
    assert second.json()["created"] is False
    assert first.json()["file_id"] == second.json()["file_id"]
    assert [key[0] for key in writer.uploads] == [WEEKLY_FOLDER_ID]


async def test_unsupported_extension_is_rejected_before_any_upload(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    override_writer: Callable[[Any], None],
) -> None:
    # Arrange
    token, project_id = await _pm_project(client, make_user, ROOT)
    writer = _writer_with_weekly_folder()
    override_writer(writer)

    # Act
    response = await client.post(
        _upload_url(project_id),
        data={"kind": "WEEKLY_REPORT"},
        files={"file": ("malware.exe", b"x", "application/octet-stream")},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 422
    assert writer.uploads == {}


async def test_upload_to_project_without_root_folder_returns_409(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    override_writer: Callable[[Any], None],
) -> None:
    # Arrange
    token, project_id = await _pm_project(client, make_user, None)
    override_writer(_writer_with_weekly_folder())

    # Act
    response = await client.post(
        _upload_url(project_id),
        data={"kind": "WEEKLY_REPORT"},
        files={"file": ("a.docx", b"x", DOCX_MIME)},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 409


async def test_missing_pmis_folder_returns_409_and_creates_nothing(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    override_writer: Callable[[Any], None],
) -> None:
    # Arrange
    token, project_id = await _pm_project(client, make_user, ROOT)
    writer = FakeDriveWriter(tree={ROOT: []})
    override_writer(writer)

    # Act
    response = await client.post(
        _upload_url(project_id),
        data={"kind": "CONTRACT"},
        files={"file": ("hop_dong.pdf", b"x", "application/pdf")},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 409
    assert writer.uploads == {}
