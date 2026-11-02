from typing import Any
from uuid import UUID

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role
from app.models.audit_log import AuditLog
from app.models.drive_file import DriveFile
from tests.integration.helpers import (
    UserFactory,
    create_project,
    login_as,
)

pytestmark = pytest.mark.integration

FILE_PAYLOAD: dict[str, Any] = {
    "stt": 1,
    "folder_path": "Tài liệu lưu trữ / 2.Thủ tục",
    "file_name": "1595_QD phe duyet du an...signed.pdf",
    "file_format": "PDF Signed",
    "storage_location": "Google Drive",
    "purpose": "Quyết định phê duyệt dự án của Sở GD&ĐT",
    "legal_status": "Bản scan ký chính thức",
    "security_ownership": "Pháp lý CĐT",
    "next_action": "Căn cứ pháp lý nghiệm thu gốc",
}


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register_url(project_id: str) -> str:
    return f"/api/v1/projects/{project_id}/file-register"


async def _pm_with_project(client: httpx.AsyncClient, make_user: UserFactory) -> tuple[str, str]:
    await make_user(email="pm-file@example.com", role=Role.PM)
    token = await login_as(client, "pm-file@example.com")
    project_id = await create_project(client, token)
    return token, project_id


async def _create_entry(
    client: httpx.AsyncClient,
    token: str,
    project_id: str,
    **overrides: Any,
) -> dict[str, Any]:
    response = await client.post(
        _register_url(project_id),
        json={**FILE_PAYLOAD, **overrides},
        headers=_bearer(token),
    )
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


async def test_pm_creates_entry_and_list_returns_it_ordered_by_stt(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    await _create_entry(client, token, project_id, stt=2, file_name="Muộn hơn")
    await _create_entry(client, token, project_id, stt=1, file_name="Đầu tiên")

    # Act
    response = await client.get(_register_url(project_id), headers=_bearer(token))

    # Assert
    assert response.status_code == 200
    assert [row["stt"] for row in response.json()] == [1, 2]
    assert response.json()[0]["drive_file_id"] is None


async def test_duplicate_stt_in_same_project_returns_409(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    await _create_entry(client, token, project_id, stt=1)

    # Act
    response = await client.post(
        _register_url(project_id), json=FILE_PAYLOAD, headers=_bearer(token)
    )

    # Assert
    assert response.status_code == 409


async def test_create_is_audited(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)

    # Act
    body = await _create_entry(client, token, project_id)

    # Assert
    audited = (
        await session.execute(select(AuditLog).where(AuditLog.action == "file_register.create"))
    ).scalar_one()
    assert audited.entity_id == body["id"]


async def test_pm_updates_entry_fields(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    body = await _create_entry(client, token, project_id)

    # Act
    response = await client.patch(
        f"{_register_url(project_id)}/{body['id']}",
        json={"next_action": "Đôn đốc Sở ký bản chính"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["next_action"] == "Đôn đốc Sở ký bản chính"


async def test_pm_links_drive_file_of_same_project(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    body = await _create_entry(client, token, project_id)
    drive_row = DriveFile(
        project_id=UUID(project_id),
        drive_file_id="file-register-link",
        file_name="1595_QD_SGDDT.pdf",
    )
    session.add(drive_row)
    await session.commit()

    # Act
    response = await client.patch(
        f"{_register_url(project_id)}/{body['id']}",
        json={"drive_file_id": str(drive_row.id)},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["drive_file_id"] == str(drive_row.id)


async def test_link_to_drive_file_of_another_project_returns_422(
    client: httpx.AsyncClient,
    make_user: UserFactory,
    session: AsyncSession,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    other_project_id = await create_project(client, token, code="OTHER-FILE-REG")
    foreign_file = DriveFile(
        project_id=UUID(other_project_id),
        drive_file_id="file-register-foreign",
        file_name="khac-du-an.pdf",
    )
    session.add(foreign_file)
    await session.commit()
    body = await _create_entry(client, token, project_id)

    # Act
    response = await client.patch(
        f"{_register_url(project_id)}/{body['id']}",
        json={"drive_file_id": str(foreign_file.id)},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 422


async def test_contractor_member_can_read_but_not_write(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    pm_token, project_id = await _pm_with_project(client, make_user)
    contractor = await make_user(email="nha-thau-file@example.com", role=Role.CONTRACTOR)
    await client.post(
        f"/api/v1/projects/{project_id}/members",
        json={"user_id": str(contractor.id), "role": Role.CONTRACTOR.value},
        headers=_bearer(pm_token),
    )
    contractor_token = await login_as(client, "nha-thau-file@example.com")

    # Act
    read = await client.get(_register_url(project_id), headers=_bearer(contractor_token))
    write = await client.post(
        _register_url(project_id), json=FILE_PAYLOAD, headers=_bearer(contractor_token)
    )

    # Assert
    assert read.status_code == 200
    assert write.status_code == 403


async def test_non_member_cannot_list_entries(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    _, project_id = await _pm_with_project(client, make_user)
    await make_user(email="nguoi-ngoai-file@example.com", role=Role.PM)
    outsider_token = await login_as(client, "nguoi-ngoai-file@example.com")

    # Act
    response = await client.get(_register_url(project_id), headers=_bearer(outsider_token))

    # Assert
    assert response.status_code == 403


async def test_unknown_entry_returns_404(
    client: httpx.AsyncClient,
    make_user: UserFactory,
) -> None:
    # Arrange
    token, project_id = await _pm_with_project(client, make_user)
    unknown_id = "00000000-0000-0000-0000-000000000000"

    # Act
    response = await client.patch(
        f"{_register_url(project_id)}/{unknown_id}",
        json={"next_action": "không tồn tại"},
        headers=_bearer(token),
    )

    # Assert
    assert response.status_code == 404
