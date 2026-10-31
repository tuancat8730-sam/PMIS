"""Nạp dữ liệu thật của dự án theo spec §7. Chạy lại an toàn: bản ghi đã có được bỏ qua."""

import asyncio
import json
import logging
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.project import Project, ProjectArchetype
from app.schemas.beneficiary_units import BeneficiaryUnitCreate
from app.schemas.milestones import MilestoneCreate
from app.schemas.projects import ProjectCreate
from app.services.audit import record_audit
from app.services.beneficiary_units import create_unit, find_unit_by_code
from app.services.milestones import create_milestone, find_milestone_by_code
from app.services.projects import create_project

logger = logging.getLogger(__name__)

SEED_DATA_DIR = Path(__file__).resolve().parent / "seed_data"
HCM_UNITS_FILE = SEED_DATA_DIR / "hcm_survey_units.json"
HCM_MILESTONES_FILE = SEED_DATA_DIR / "hcm_milestones.json"

HCM_PROJECT = ProjectCreate(
    code="SGD-HCM-CSVC-2026",
    name="Xây dựng hệ thống quản lý dữ liệu về cơ sở vật chất và thiết bị trường học",
    short_name="SGD-HCM CSVC 2026",
    archetype=ProjectArchetype.IT_SYSTEM,
    investor_name="Sở GD&ĐT TP.HCM",
    total_investment=Decimal("5999498939.00"),
)


def load_seed_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        rows = json.load(handle)
    if not isinstance(rows, list):
        raise ValueError(f"File seed {path.name} phải là danh sách bản ghi")
    return rows


def load_units(path: Path) -> list[dict[str, Any]]:
    return load_seed_rows(path)


async def find_project_by_code(session: AsyncSession, code: str) -> Project | None:
    result = await session.execute(select(Project).where(Project.code == code))
    return result.scalar_one_or_none()


async def ensure_project(session: AsyncSession, payload: ProjectCreate) -> Project:
    existing = await find_project_by_code(session, payload.code)
    if existing is not None:
        return existing
    project = await create_project(session, payload=payload)
    await record_audit(
        session,
        actor_id=None,
        action="project.seed",
        entity_type="project",
        entity_id=str(project.id),
        changes={"code": project.code},
    )
    return project


async def ensure_units(session: AsyncSession, project_id: UUID, rows: list[dict[str, Any]]) -> int:
    inserted = 0
    for row in rows:
        payload = BeneficiaryUnitCreate(**row)
        if await find_unit_by_code(session, project_id, payload.unit_code) is not None:
            continue
        unit = await create_unit(session, project_id=project_id, values=payload.model_dump())
        await record_audit(
            session,
            actor_id=None,
            action="beneficiary_unit.seed",
            entity_type="beneficiary_unit",
            entity_id=str(unit.id),
            changes={"unit_code": unit.unit_code},
        )
        inserted += 1
    return inserted


async def ensure_milestones(
    session: AsyncSession, project_id: UUID, rows: list[dict[str, Any]]
) -> int:
    inserted = 0
    for row in rows:
        payload = MilestoneCreate(**row)
        if await find_milestone_by_code(session, project_id, payload.code) is not None:
            continue
        milestone = await create_milestone(
            session, project_id=project_id, values=payload.model_dump()
        )
        await record_audit(
            session,
            actor_id=None,
            action="milestone.seed",
            entity_type="milestone",
            entity_id=str(milestone.id),
            changes={"code": milestone.code},
        )
        inserted += 1
    return inserted


async def seed_hcm_project(session_factory: async_sessionmaker[AsyncSession]) -> int:
    """Nạp SGD-HCM, 8 đơn vị khảo sát và mốc đã biết trong một transaction; trả về số đơn vị mới."""
    async with session_factory() as session:
        project = await ensure_project(session, HCM_PROJECT)
        inserted = await ensure_units(session, project.id, load_units(HCM_UNITS_FILE))
        milestones = await ensure_milestones(
            session, project.id, load_seed_rows(HCM_MILESTONES_FILE)
        )
        await session.commit()
    logger.info("Seed %s: thêm %d đơn vị thụ hưởng, %d mốc", HCM_PROJECT.code, inserted, milestones)
    return inserted


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)

    async def _run() -> None:
        try:
            await seed_hcm_project(async_sessionmaker(engine, expire_on_commit=False))
        finally:
            await engine.dispose()

    asyncio.run(_run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
