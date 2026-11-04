import pytest
from fastapi import FastAPI
from sqlalchemy import func, select

from app.db.seed_real_projects import seed_hcm_project, seed_lam_dong_project
from app.models.project import Project
from app.models.project_file_register import ProjectFileRegisterEntry

pytestmark = pytest.mark.integration

HCM_FILE_ENTRY_COUNT = 20
LAM_DONG_FILE_ENTRY_COUNT = 25
LAM_DONG_CODE = "SGD-LD-TB10-2026"


async def _count_entries(app: FastAPI, project_code: str) -> int:
    async with app.state.session_factory() as session:
        project_id = (
            await session.execute(select(Project.id).where(Project.code == project_code))
        ).scalar_one()
        return int(
            (
                await session.execute(
                    select(func.count(ProjectFileRegisterEntry.id)).where(
                        ProjectFileRegisterEntry.project_id == project_id
                    )
                )
            ).scalar_one()
        )


async def test_seed_creates_hcm_file_register_and_is_idempotent(app: FastAPI) -> None:
    # Arrange
    session_factory = app.state.session_factory

    # Act
    await seed_hcm_project(session_factory)
    await seed_hcm_project(session_factory)

    # Assert
    async with session_factory() as session:
        entries = (await session.execute(select(ProjectFileRegisterEntry))).scalars().all()
    by_stt = {entry.stt: entry for entry in entries}
    assert len(entries) == HCM_FILE_ENTRY_COUNT
    assert by_stt[1].file_name == "Checklist ho so - SGD TPHCM.xlsx"
    assert by_stt[1].storage_location == "Local & Drive"
    assert by_stt[20].folder_path == "Thư mục gốc"


async def test_seed_creates_lam_dong_file_register_with_report_statuses(app: FastAPI) -> None:
    # Arrange
    session_factory = app.state.session_factory

    # Act
    await seed_lam_dong_project(session_factory)

    # Assert
    assert await _count_entries(app, LAM_DONG_CODE) == LAM_DONG_FILE_ENTRY_COUNT
    async with session_factory() as session:
        project_id = (
            await session.execute(select(Project.id).where(Project.code == LAM_DONG_CODE))
        ).scalar_one()
        entries = (
            (
                await session.execute(
                    select(ProjectFileRegisterEntry).where(
                        ProjectFileRegisterEntry.project_id == project_id
                    )
                )
            )
            .scalars()
            .all()
        )
    # Báo cáo 04/11/2026 có tình trạng pháp lý và hành động cho mọi dòng register.
    assert all(entry.legal_status for entry in entries)
    serial_entry = next(entry for entry in entries if entry.stt == 9)
    assert "1.420 serial" in serial_entry.next_action
