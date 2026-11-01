"""Cấu hình worker ARQ: job và lịch quét Drive.

Chạy bằng: arq app.worker.settings.WorkerSettings
"""

from typing import Any

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.integrations.drive import GoogleDriveGateway
from app.worker.drive_jobs import sync_all_drive_projects_job, sync_project_drive_job

# Quét Drive mỗi 15 phút, theo mục G2 của plan E5.
DRIVE_SWEEP_MINUTES = frozenset(range(0, 60, 15))


async def startup(ctx: dict[str, Any]) -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    ctx["engine"] = engine
    ctx["session_factory"] = async_sessionmaker(engine, expire_on_commit=False)
    key_file_path = settings.drive_service_account_file
    ctx["drive_gateway"] = (
        GoogleDriveGateway.from_service_account_file(key_file_path) if key_file_path else None
    )


async def shutdown(ctx: dict[str, Any]) -> None:
    await ctx["engine"].dispose()


class WorkerSettings:
    functions = [sync_project_drive_job]
    cron_jobs = [cron(sync_all_drive_projects_job, minute=DRIVE_SWEEP_MINUTES)]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
