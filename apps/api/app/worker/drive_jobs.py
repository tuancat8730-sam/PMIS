"""Job nền ARQ cho đồng bộ Drive. Mỗi dự án có một session và một lần commit riêng.

Một dự án lỗi không làm dừng lịch quét: lỗi được log và đếm, các dự án còn lại vẫn chạy tiếp.
"""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.integrations.drive import DriveApiError
from app.models.project import Project
from app.services.drive_sync import DriveRootNotConfiguredError, sync_project_drive

logger = logging.getLogger(__name__)

JobContext = dict[str, Any]
STATUS_OK = "ok"
STATUS_ERROR = "error"
STATUS_NO_ROOT = "no_root"
STATUS_NOT_FOUND = "not_found"


async def sync_project_drive_job(ctx: JobContext, project_id: str) -> dict[str, Any]:
    gateway = ctx.get("drive_gateway")
    if gateway is None:
        logger.warning("Bỏ qua đồng bộ Drive: chưa cấu hình tài khoản dịch vụ")
        return {"status": STATUS_ERROR, "created": 0, "updated": 0}

    async with ctx["session_factory"]() as session:
        project = await session.get(Project, UUID(project_id))
        if project is None:
            return {"status": STATUS_NOT_FOUND, "created": 0, "updated": 0}
        try:
            result = await sync_project_drive(session, gateway, project)
        except DriveRootNotConfiguredError:
            return {"status": STATUS_NO_ROOT, "created": 0, "updated": 0}
        except DriveApiError as error:
            await session.rollback()
            logger.error("Đồng bộ Drive thất bại: project=%s status=%s", project_id, error.status)
            return {"status": STATUS_ERROR, "created": 0, "updated": 0}
        await session.commit()

    return {"status": STATUS_OK, "created": result.created, "updated": result.updated}


async def sync_all_drive_projects_job(ctx: JobContext) -> dict[str, int]:
    if ctx.get("drive_gateway") is None:
        logger.warning("Bỏ qua lịch quét Drive: chưa cấu hình tài khoản dịch vụ")
        return {"projects": 0, "failed": 0}

    async with ctx["session_factory"]() as session:
        result = await session.execute(
            select(Project.id).where(Project.drive_root_folder_id.is_not(None))
        )
        project_ids = [str(project_id) for project_id in result.scalars().all()]

    failed = 0
    for project_id in project_ids:
        outcome = await sync_project_drive_job(ctx, project_id)
        if outcome["status"] != STATUS_OK:
            failed += 1
    return {"projects": len(project_ids), "failed": failed}
