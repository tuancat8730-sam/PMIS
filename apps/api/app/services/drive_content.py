"""Tải nội dung file Drive để xem trực tiếp trong tool (chỉ đọc, không ghi DB).

Kiểm tra trạng thái đã xóa và thuộc dự án nằm ở đây, nên endpoint không thể bỏ qua.
Gọi Drive là I/O đồng bộ, nên chuyển sang threadpool để không chặn event loop.
"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.drive_file_kinds import classify_file
from app.core.drive_preview_rules import (
    PREVIEW_MAX_BYTES,
    DrivePreviewTooLargeError,
    check_preview_size,
    preview_media_type,
)
from app.integrations.drive_gateway import DriveGateway
from app.models.drive_file import DriveFile


class DriveFileNotFoundError(Exception):
    """File không tồn tại trong dự án, hoặc đã bị xóa trên Drive."""


@dataclass(frozen=True)
class DrivePreview:
    content: bytes
    media_type: str
    file_name: str


async def load_drive_file_preview(
    session: AsyncSession,
    gateway: DriveGateway,
    project_id: UUID,
    drive_file_id: str,
) -> DrivePreview:
    row = await _find_active_file(session, project_id, drive_file_id)
    media_type = preview_media_type(classify_file(row.file_name))
    check_preview_size(row.file_size)
    content = await run_in_threadpool(gateway.download, drive_file_id)
    if len(content) > PREVIEW_MAX_BYTES:
        # Kích thước thật có thể khác bản ghi đồng bộ, nên kiểm tra lại sau khi tải.
        raise DrivePreviewTooLargeError("File vượt quá giới hạn xem trực tiếp")
    return DrivePreview(content=content, media_type=media_type, file_name=row.file_name)


async def _find_active_file(
    session: AsyncSession,
    project_id: UUID,
    drive_file_id: str,
) -> DriveFile:
    result = await session.execute(
        select(DriveFile).where(
            DriveFile.project_id == project_id,
            DriveFile.drive_file_id == drive_file_id,
            DriveFile.removed_at.is_(None),
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise DriveFileNotFoundError(drive_file_id)
    return row
