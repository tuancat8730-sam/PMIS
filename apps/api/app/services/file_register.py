from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.drive_file import DriveFile
from app.models.project_file_register import ProjectFileRegisterEntry


class DuplicateSttError(Exception):
    """Số thứ tự (`stt`) đã tồn tại trong register của dự án."""


class ForeignDriveFileError(Exception):
    """File Drive được liên kết không thuộc dự án này."""


async def list_file_entries(
    session: AsyncSession,
    project_id: UUID,
) -> list[ProjectFileRegisterEntry]:
    result = await session.execute(
        select(ProjectFileRegisterEntry)
        .where(ProjectFileRegisterEntry.project_id == project_id)
        .order_by(ProjectFileRegisterEntry.stt)
    )
    return list(result.scalars().all())


async def get_file_entry(
    session: AsyncSession,
    project_id: UUID,
    entry_id: UUID,
) -> ProjectFileRegisterEntry | None:
    result = await session.execute(
        select(ProjectFileRegisterEntry).where(
            ProjectFileRegisterEntry.id == entry_id,
            ProjectFileRegisterEntry.project_id == project_id,
        )
    )
    return result.scalar_one_or_none()


async def ensure_drive_file_in_project(
    session: AsyncSession,
    project_id: UUID,
    drive_file_id: UUID | None,
) -> None:
    """Chỉ cho liên kết file Drive thuộc cùng dự án. `None` nghĩa là bỏ liên kết, luôn hợp lệ."""
    if drive_file_id is None:
        return
    result = await session.execute(
        select(DriveFile.id).where(
            DriveFile.id == drive_file_id,
            DriveFile.project_id == project_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise ForeignDriveFileError(str(drive_file_id))


async def create_file_entry(
    session: AsyncSession,
    *,
    project_id: UUID,
    values: Mapping[str, Any],
) -> ProjectFileRegisterEntry:
    entry = ProjectFileRegisterEntry(project_id=project_id, **values)
    session.add(entry)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise DuplicateSttError(str(values["stt"])) from exc
    return entry


def update_file_entry(entry: ProjectFileRegisterEntry, changes: Mapping[str, Any]) -> None:
    for field, value in changes.items():
        setattr(entry, field, value)
