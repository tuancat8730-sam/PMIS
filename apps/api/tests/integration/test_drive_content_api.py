from collections.abc import Callable, Iterator
from typing import Any

import httpx
import pytest
from fastapi import FastAPI

from app.api.v1.drive import get_drive_gateway
from app.core.drive_preview_rules import PREVIEW_MAX_BYTES
from app.core.rbac import Role
from app.integrations.drive import DriveApiError
from app.integrations.drive_gateway import DriveEntry
from tests.fakes.fake_drive_gateway import FakeDriveGateway
from tests.integration.helpers import UserFactory, create_project, login_as

pytestmark = pytest.mark.integration

ROOT = "root-folder-content"
OTHER_ROOT = "root-folder-other"
PM_EMAIL = "pm-content@example.com"
OUTSIDER_EMAIL = "outsider-content@example.com"
PDF_BYTES = b"%PDF-1.4 noi dung thu"
IMAGE_BYTES = b"\xff\xd8\xff\xe0 anh thu"


class _FailingDownloadGateway(FakeDriveGateway):
    def download(self, drive_file_id: str) -> bytes:
        raise DriveApiError(403, "Drive trả lỗi 403 khi tải file")


def _entry(file_id: str, name: str, parent: str, size: int = 512) -> DriveEntry:
    return DriveEntry(
        drive_file_id=file_id,
        parent_id=parent,
        name=name,
        mime_type="application/octet-stream",
        size=size,
        web_view_link=f"https://drive.example/{file_id}",
        modified_time="2026-10-01T00:00:00Z",
        is_folder=False,
    )


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _sync_url(project_id: str) -> str:
    return f"/api/v1/projects/{project_id}/drive/sync"


def _content_url(project_id: str, drive_file_id: str) -> str:
    return f"/api/v1/projects/{project_id}/drive/files/{drive_file_id}/content"


@pytest.fixture
def override_gateway(app: FastAPI) -> Iterator[Callable[[Any], None]]:
    def _set(gateway: Any) -> None:
        app.dependency_overrides[get_drive_gateway] = lambda: gateway

    yield _set
    app.dependency_overrides.pop(get_drive_gateway, None)


async def _pm_project_with_files(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    override_gateway: Callable[[Any], None],
    entries: list[DriveEntry],
    contents: dict[str, bytes],
) -> tuple[str, str]:
    await make_user(email=PM_EMAIL, role=Role.PM)
    token = await login_as(client, PM_EMAIL)
    project_id = await create_project(client, token, drive_root_folder_id=ROOT)
    override_gateway(FakeDriveGateway({ROOT: entries}, contents=contents))
    sync = await client.post(_sync_url(project_id), headers=_bearer(token))
    assert sync.status_code == 200, sync.text
    return project_id, token


async def test_member_gets_pdf_inline_with_security_headers(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    override_gateway: Callable[[Any], None],
) -> None:
    # Arrange
    project_id, token = await _pm_project_with_files(
        client,
        make_user,
        override_gateway,
        [_entry("pdf-1", "bien_ban.pdf", ROOT)],
        {"pdf-1": PDF_BYTES},
    )

    # Act
    response = await client.get(_content_url(project_id, "pdf-1"), headers=_bearer(token))

    # Assert
    assert response.status_code == 200, response.text
    assert response.content == PDF_BYTES
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"].startswith("inline")
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["x-content-type-options"] == "nosniff"


async def test_image_is_served_with_image_mime_type(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    override_gateway: Callable[[Any], None],
) -> None:
    # Arrange
    project_id, token = await _pm_project_with_files(
        client,
        make_user,
        override_gateway,
        [_entry("img-1", "hien_truong.jpg", ROOT)],
        {"img-1": IMAGE_BYTES},
    )

    # Act
    response = await client.get(_content_url(project_id, "img-1"), headers=_bearer(token))

    # Assert
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "image/jpeg"


async def test_docx_file_is_not_previewable_and_returns_415(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    override_gateway: Callable[[Any], None],
) -> None:
    # Arrange
    project_id, token = await _pm_project_with_files(
        client,
        make_user,
        override_gateway,
        [_entry("doc-1", "bao_cao.docx", ROOT)],
        {"doc-1": b"PK docx"},
    )

    # Act
    response = await client.get(_content_url(project_id, "doc-1"), headers=_bearer(token))

    # Assert
    assert response.status_code == 415


async def test_file_of_another_project_is_not_found(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    override_gateway: Callable[[Any], None],
) -> None:
    # Arrange
    await make_user(email=PM_EMAIL, role=Role.PM)
    token = await login_as(client, PM_EMAIL)
    project_a = await create_project(client, token, drive_root_folder_id=ROOT, code="SGD-A-CONTENT")
    project_b = await create_project(
        client, token, drive_root_folder_id=OTHER_ROOT, code="SGD-B-CONTENT"
    )
    override_gateway(
        FakeDriveGateway(
            {
                ROOT: [_entry("pdf-a", "a.pdf", ROOT)],
                OTHER_ROOT: [_entry("pdf-b", "b.pdf", OTHER_ROOT)],
            },
            contents={"pdf-a": PDF_BYTES, "pdf-b": PDF_BYTES},
        )
    )
    await client.post(_sync_url(project_a), headers=_bearer(token))
    await client.post(_sync_url(project_b), headers=_bearer(token))

    # Act
    response = await client.get(_content_url(project_a, "pdf-b"), headers=_bearer(token))

    # Assert
    assert response.status_code == 404


async def test_file_removed_from_drive_is_not_found(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    override_gateway: Callable[[Any], None],
) -> None:
    # Arrange
    project_id, token = await _pm_project_with_files(
        client,
        make_user,
        override_gateway,
        [_entry("pdf-1", "bien_ban.pdf", ROOT)],
        {"pdf-1": PDF_BYTES},
    )
    override_gateway(FakeDriveGateway({ROOT: []}, contents={}))
    await client.post(_sync_url(project_id), headers=_bearer(token))

    # Act
    response = await client.get(_content_url(project_id, "pdf-1"), headers=_bearer(token))

    # Assert
    assert response.status_code == 404


async def test_file_over_size_limit_returns_413(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    override_gateway: Callable[[Any], None],
) -> None:
    # Arrange
    project_id, token = await _pm_project_with_files(
        client,
        make_user,
        override_gateway,
        [_entry("big-1", "ban_ve_lon.pdf", ROOT, size=PREVIEW_MAX_BYTES + 1)],
        {"big-1": PDF_BYTES},
    )

    # Act
    response = await client.get(_content_url(project_id, "big-1"), headers=_bearer(token))

    # Assert
    assert response.status_code == 413


async def test_drive_download_failure_returns_502(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    override_gateway: Callable[[Any], None],
) -> None:
    # Arrange
    project_id, token = await _pm_project_with_files(
        client,
        make_user,
        override_gateway,
        [_entry("pdf-1", "bien_ban.pdf", ROOT)],
        {"pdf-1": PDF_BYTES},
    )
    override_gateway(_FailingDownloadGateway({ROOT: [_entry("pdf-1", "bien_ban.pdf", ROOT)]}))

    # Act
    response = await client.get(_content_url(project_id, "pdf-1"), headers=_bearer(token))

    # Assert
    assert response.status_code == 502


async def test_user_outside_project_gets_403(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    override_gateway: Callable[[Any], None],
) -> None:
    # Arrange
    project_id, _ = await _pm_project_with_files(
        client,
        make_user,
        override_gateway,
        [_entry("pdf-1", "bien_ban.pdf", ROOT)],
        {"pdf-1": PDF_BYTES},
    )
    await make_user(email=OUTSIDER_EMAIL, role=Role.INVESTOR)
    outsider_token = await login_as(client, OUTSIDER_EMAIL)

    # Act
    response = await client.get(_content_url(project_id, "pdf-1"), headers=_bearer(outsider_token))

    # Assert
    assert response.status_code == 403


async def test_download_flag_serves_docx_as_attachment(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    override_gateway: Callable[[Any], None],
) -> None:
    # Arrange
    docx_bytes = b"PK\x03\x04 noi dung docx"
    project_id, token = await _pm_project_with_files(
        client,
        make_user,
        override_gateway,
        [_entry("doc-1", "bao_cao.docx", ROOT)],
        {"doc-1": docx_bytes},
    )

    # Act
    response = await client.get(
        f"{_content_url(project_id, 'doc-1')}?download=true", headers=_bearer(token)
    )

    # Assert
    assert response.status_code == 200, response.text
    assert response.content == docx_bytes
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.wordprocessingml"
    )
    assert response.headers["content-disposition"].startswith("attachment")
