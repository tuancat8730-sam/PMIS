"""Đồng bộ cây thư mục Drive của dự án vào bảng `drive_files` (chiều Drive → App).

Service không commit: router hoặc job nền quyết định commit để thao tác và audit cùng transaction.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.drive_match_rules import DriveMatchSuggestion, MatchableDocument, suggest_matches
from app.core.drive_tree import DriveFileSnapshot, plan_sync, walk_tree
from app.integrations.drive_gateway import DriveGateway
from app.models.drive_file import DriveFile
from app.models.legal_document import LegalDocument
from app.models.project import Project


class DriveRootNotConfiguredError(Exception):
    """Dự án chưa có `drive_root_folder_id`, không quét được."""


@dataclass(frozen=True)
class DriveSyncResult:
    scanned: int
    created: int
    updated: int


async def sync_project_drive(
    session: AsyncSession,
    gateway: DriveGateway,
    project: Project,
) -> DriveSyncResult:
    root_folder_id = project.drive_root_folder_id
    if root_folder_id is None:
        raise DriveRootNotConfiguredError(str(project.id))

    snapshots = walk_tree(gateway, root_folder_id)
    stored_rows = await _load_rows_by_drive_id(session, project.id)
    plan = plan_sync(_stored_fields(stored_rows), snapshots)

    synced_at = datetime.now(UTC)
    for snapshot in plan.to_create:
        session.add(_new_row(project.id, snapshot, synced_at))
    for snapshot in plan.to_update:
        _apply_snapshot(stored_rows[snapshot.drive_file_id], snapshot, synced_at)

    return DriveSyncResult(
        scanned=len(snapshots),
        created=len(plan.to_create),
        updated=len(plan.to_update),
    )


async def suggest_drive_matches(
    session: AsyncSession,
    project_id: Any,
) -> list[DriveMatchSuggestion]:
    """Gợi ý file Drive khớp đầu mục checklist. Chỉ đọc, không đổi trạng thái hồ sơ."""
    file_rows = await session.execute(
        select(DriveFile.drive_file_id, DriveFile.file_name).where(
            DriveFile.project_id == project_id
        )
    )
    document_rows = await session.execute(
        select(LegalDocument.id, LegalDocument.doc_code_symbol, LegalDocument.doc_name).where(
            LegalDocument.project_id == project_id
        )
    )
    files = [(row.drive_file_id, row.file_name) for row in file_rows]
    documents = [
        MatchableDocument(
            document_id=row.id,
            doc_code_symbol=row.doc_code_symbol,
            doc_name=row.doc_name,
        )
        for row in document_rows
    ]
    return suggest_matches(files, documents)


async def list_project_drive_files(session: AsyncSession, project_id: Any) -> list[DriveFile]:
    result = await session.execute(
        select(DriveFile).where(DriveFile.project_id == project_id).order_by(DriveFile.drive_path)
    )
    return list(result.scalars().all())


async def _load_rows_by_drive_id(session: AsyncSession, project_id: Any) -> dict[str, DriveFile]:
    result = await session.execute(select(DriveFile).where(DriveFile.project_id == project_id))
    return {row.drive_file_id: row for row in result.scalars().all()}


def _stored_fields(rows: dict[str, DriveFile]) -> dict[str, dict[str, Any]]:
    return {
        drive_file_id: {
            "file_name": row.file_name,
            "drive_path": row.drive_path,
            "modified_time": row.modified_time,
        }
        for drive_file_id, row in rows.items()
    }


def _new_row(project_id: Any, snapshot: DriveFileSnapshot, synced_at: datetime) -> DriveFile:
    return DriveFile(
        project_id=project_id,
        drive_file_id=snapshot.drive_file_id,
        drive_parent_id=snapshot.drive_parent_id,
        file_name=snapshot.file_name,
        drive_path=snapshot.drive_path,
        mime_type=snapshot.mime_type,
        file_size=snapshot.file_size,
        web_view_link=snapshot.web_view_link,
        modified_time=snapshot.modified_time,
        last_synced_at=synced_at,
    )


def _apply_snapshot(row: DriveFile, snapshot: DriveFileSnapshot, synced_at: datetime) -> None:
    row.drive_parent_id = snapshot.drive_parent_id
    row.file_name = snapshot.file_name
    row.drive_path = snapshot.drive_path
    row.mime_type = snapshot.mime_type
    row.file_size = snapshot.file_size
    row.web_view_link = snapshot.web_view_link
    row.modified_time = snapshot.modified_time
    row.last_synced_at = synced_at
