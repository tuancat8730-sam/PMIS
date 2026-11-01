from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.drive_gateway import DriveEntry
from app.models.drive_file import DriveFile
from app.models.project import Project, ProjectArchetype
from app.services.drive_sync import DriveRootNotConfiguredError, sync_project_drive
from tests.fakes.fake_drive_gateway import FakeDriveGateway

pytestmark = pytest.mark.integration

ROOT = "root-folder-sgd"
FOLDER_MIME = "application/vnd.google-apps.folder"


def _pdf(
    file_id: str, name: str, parent: str, modified: str = "2026-10-01T00:00:00Z"
) -> DriveEntry:
    return DriveEntry(
        drive_file_id=file_id,
        parent_id=parent,
        name=name,
        mime_type="application/pdf",
        size=1024,
        web_view_link=f"https://drive.example/{file_id}",
        modified_time=modified,
        is_folder=False,
    )


def _folder(folder_id: str, name: str, parent: str) -> DriveEntry:
    return DriveEntry(
        drive_file_id=folder_id,
        parent_id=parent,
        name=name,
        mime_type=FOLDER_MIME,
        size=None,
        web_view_link=None,
        modified_time="2026-10-01T00:00:00Z",
        is_folder=True,
    )


async def _make_project(session: AsyncSession, drive_root_folder_id: str | None) -> Project:
    project = Project(
        code="SGD-HCM-DRIVE-TEST",
        name="Dự án thử nghiệm Drive",
        short_name="Thử nghiệm Drive",
        archetype=ProjectArchetype.GOODS_PROCUREMENT,
        investor_name="Sở GD&ĐT TP.HCM",
        total_investment=Decimal("1000000.00"),
        drive_root_folder_id=drive_root_folder_id,
    )
    session.add(project)
    await session.commit()
    return project


async def _stored_files(session: AsyncSession, project: Project) -> list[DriveFile]:
    result = await session.execute(
        select(DriveFile)
        .where(DriveFile.project_id == project.id)
        .order_by(DriveFile.drive_file_id)
    )
    return list(result.scalars().all())


async def test_first_sync_stores_supported_files_and_skips_others(session: AsyncSession) -> None:
    # Arrange
    project = await _make_project(session, ROOT)
    gateway = FakeDriveGateway(
        {
            ROOT: [
                _folder("sub", "5.Nghiem thu", ROOT),
                _pdf("a", "tong_hop.pdf", ROOT),
                _pdf("t", "ghi_chu.txt", ROOT),
            ],
            "sub": [_pdf("b", "bien_ban.pdf", "sub")],
        }
    )

    # Act
    result = await sync_project_drive(session, gateway, project)
    await session.commit()

    # Assert
    assert (result.created, result.updated) == (2, 0)
    stored = await _stored_files(session, project)
    assert [(row.drive_file_id, row.drive_path) for row in stored] == [
        ("a", "tong_hop.pdf"),
        ("b", "5.Nghiem thu/bien_ban.pdf"),
    ]


async def test_second_sync_of_same_tree_creates_no_duplicates(session: AsyncSession) -> None:
    # Arrange
    project = await _make_project(session, ROOT)
    gateway = FakeDriveGateway({ROOT: [_pdf("a", "tong_hop.pdf", ROOT)]})
    await sync_project_drive(session, gateway, project)
    await session.commit()

    # Act
    result = await sync_project_drive(session, gateway, project)
    await session.commit()

    # Assert
    assert (result.created, result.updated) == (0, 0)
    assert len(await _stored_files(session, project)) == 1


async def test_renamed_file_is_updated_in_place(session: AsyncSession) -> None:
    # Arrange
    project = await _make_project(session, ROOT)
    await sync_project_drive(
        session, FakeDriveGateway({ROOT: [_pdf("a", "cu.pdf", ROOT)]}), project
    )
    await session.commit()
    renamed = FakeDriveGateway(
        {ROOT: [_pdf("a", "moi.pdf", ROOT, modified="2026-10-05T08:00:00Z")]}
    )

    # Act
    result = await sync_project_drive(session, renamed, project)
    await session.commit()

    # Assert
    assert (result.created, result.updated) == (0, 1)
    stored = await _stored_files(session, project)
    assert [row.file_name for row in stored] == ["moi.pdf"]
    assert stored[0].modified_time == datetime(2026, 10, 5, 8, 0, tzinfo=UTC)


async def test_sync_without_root_folder_is_rejected(session: AsyncSession) -> None:
    # Arrange
    project = await _make_project(session, None)
    gateway = FakeDriveGateway({})

    # Act / Assert
    with pytest.raises(DriveRootNotConfiguredError):
        await sync_project_drive(session, gateway, project)
