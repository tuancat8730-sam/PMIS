from decimal import Decimal
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.drive import DriveApiError
from app.integrations.drive_gateway import DriveEntry
from app.models.drive_file import DriveFile
from app.models.project import Project, ProjectArchetype
from app.worker.drive_jobs import sync_all_drive_projects_job, sync_project_drive_job
from tests.fakes.fake_drive_gateway import FakeDriveGateway

pytestmark = pytest.mark.integration

GOOD_ROOT = "root-tot"
BAD_ROOT = "root-loi"


class _SelectiveGateway:
    """Cây Drive trong bộ nhớ, nhưng một thư mục gốc luôn trả lỗi để kiểm tra cô lập lỗi."""

    def __init__(self, inner: FakeDriveGateway, failing_root: str) -> None:
        self._inner = inner
        self._failing_root = failing_root

    def list_children(self, folder_id: str) -> list[DriveEntry]:
        if folder_id == self._failing_root:
            raise DriveApiError(503, "Drive trả lỗi 503 khi đọc thư mục")
        return self._inner.list_children(folder_id)


def _pdf(file_id: str, parent: str) -> DriveEntry:
    return DriveEntry(
        drive_file_id=file_id,
        parent_id=parent,
        name=f"{file_id}.pdf",
        mime_type="application/pdf",
        size=10,
        web_view_link=None,
        modified_time="2026-10-01T00:00:00Z",
        is_folder=False,
    )


async def _make_project(session: AsyncSession, code: str, root: str | None) -> Project:
    project = Project(
        code=code,
        name=f"Dự án {code}",
        short_name=code,
        archetype=ProjectArchetype.GOODS_PROCUREMENT,
        investor_name="Sở GD&ĐT",
        total_investment=Decimal("1000.00"),
        drive_root_folder_id=root,
    )
    session.add(project)
    await session.commit()
    return project


async def _drive_file_ids(session: AsyncSession, project: Project) -> list[str]:
    result = await session.execute(select(DriveFile).where(DriveFile.project_id == project.id))
    return sorted(row.drive_file_id for row in result.scalars().all())


def _ctx(session_factory: Any, gateway: Any) -> dict[str, Any]:
    return {"session_factory": session_factory, "drive_gateway": gateway}


async def test_sync_job_stores_files_for_one_project(
    session: AsyncSession,
    app: Any,
) -> None:
    # Arrange
    project = await _make_project(session, "SGD-JOB-ONE", GOOD_ROOT)
    gateway = FakeDriveGateway({GOOD_ROOT: [_pdf("p1", GOOD_ROOT)]})

    # Act
    result = await sync_project_drive_job(_ctx(app.state.session_factory, gateway), str(project.id))

    # Assert
    assert result == {"status": "ok", "created": 1, "updated": 0}
    assert await _drive_file_ids(session, project) == ["p1"]


async def test_scheduled_sweep_continues_after_one_project_fails(
    session: AsyncSession,
    app: Any,
) -> None:
    # Arrange
    failing = await _make_project(session, "SGD-SWEEP-BAD", BAD_ROOT)
    healthy = await _make_project(session, "SGD-SWEEP-GOOD", GOOD_ROOT)
    inner = FakeDriveGateway({GOOD_ROOT: [_pdf("g1", GOOD_ROOT)]})
    gateway = _SelectiveGateway(inner, failing_root=BAD_ROOT)

    # Act
    summary = await sync_all_drive_projects_job(_ctx(app.state.session_factory, gateway))

    # Assert
    assert summary == {"projects": 2, "failed": 1}
    assert await _drive_file_ids(session, healthy) == ["g1"]
    assert await _drive_file_ids(session, failing) == []


async def test_sweep_without_configured_gateway_is_skipped(
    session: AsyncSession,
    app: Any,
) -> None:
    # Arrange
    await _make_project(session, "SGD-SKIP", GOOD_ROOT)

    # Act
    summary = await sync_all_drive_projects_job(_ctx(app.state.session_factory, None))

    # Assert
    assert summary == {"projects": 0, "failed": 0}
