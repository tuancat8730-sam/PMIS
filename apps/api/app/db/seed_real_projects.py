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
from app.models.contract import Contract
from app.models.project import Project, ProjectArchetype
from app.models.risk_issue import RiskIssue
from app.schemas.beneficiary_units import BeneficiaryUnitCreate
from app.schemas.contracts import ContractCreate
from app.schemas.milestones import MilestoneCreate
from app.schemas.projects import ProjectCreate
from app.schemas.risk_issues import RiskIssueCreate
from app.services.audit import record_audit
from app.services.beneficiary_units import create_unit, find_unit_by_code
from app.services.contracts import create_contract
from app.services.milestones import create_milestone, find_milestone_by_code
from app.services.projects import create_project
from app.services.risk_issues import create_risk_issue

logger = logging.getLogger(__name__)

SEED_DATA_DIR = Path(__file__).resolve().parent / "seed_data"
HCM_UNITS_FILE = SEED_DATA_DIR / "hcm_survey_units.json"
HCM_MILESTONES_FILE = SEED_DATA_DIR / "hcm_milestones.json"
HCM_CONTRACTS_FILE = SEED_DATA_DIR / "hcm_contracts.json"
HCM_RISKS_FILE = SEED_DATA_DIR / "hcm_risks.json"
LAM_DONG_UNITS_FILE = SEED_DATA_DIR / "lam_dong_units.json"
LAM_DONG_CONTRACTS_FILE = SEED_DATA_DIR / "lam_dong_contracts.json"
LAM_DONG_MILESTONES_FILE = SEED_DATA_DIR / "lam_dong_milestones.json"
LAM_DONG_RISKS_FILE = SEED_DATA_DIR / "lam_dong_risks.json"

HCM_PROJECT = ProjectCreate(
    code="SGD-HCM-CSVC-2026",
    name="Xây dựng hệ thống quản lý dữ liệu về cơ sở vật chất và thiết bị trường học",
    short_name="SGD-HCM CSVC 2026",
    archetype=ProjectArchetype.IT_SYSTEM,
    investor_name="Sở GD&ĐT TP.HCM",
    total_investment=Decimal("5999498939.00"),
)

# total_investment tạm lấy bằng giá gói thầu chính (HĐ HD2600226555); thay bằng TMĐT
# trong QĐ 2891/QĐ-UBND khi có số liệu, vì TMĐT chưa được xác nhận trong tài liệu.
LAM_DONG_PROJECT = ProjectCreate(
    code="SGD-LD-TB10-2026",
    name="Mua sắm trang thiết bị dạy học tối thiểu trên địa bàn tỉnh Lâm Đồng",
    short_name="SGD Lâm Đồng - Thiết bị Lớp 10",
    archetype=ProjectArchetype.GOODS_PROCUREMENT,
    investor_name="Sở Giáo dục và Đào tạo tỉnh Lâm Đồng",
    decision_authority="UBND tỉnh Lâm Đồng",
    total_investment=Decimal("106225000000.00"),
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


async def ensure_risks(session: AsyncSession, project: Project, rows: list[dict[str, Any]]) -> int:
    """Thêm rủi ro còn thiếu theo tiêu đề, không tạo trùng khi chạy lại."""
    existing_titles = set(
        (
            await session.execute(select(RiskIssue.title).where(RiskIssue.project_id == project.id))
        ).scalars()
    )
    inserted = 0
    for row in rows:
        payload = RiskIssueCreate(**row)
        if payload.title in existing_titles:
            continue
        risk = await create_risk_issue(
            session,
            project_id=project.id,
            project_code=project.code,
            values=payload.model_dump(),
        )
        await record_audit(
            session,
            actor_id=None,
            action="risk_issue.seed",
            entity_type="risk_issue",
            entity_id=str(risk.id),
            changes={"code": risk.code},
        )
        inserted += 1
    return inserted


async def ensure_contracts(
    session: AsyncSession, project_id: UUID, rows: list[dict[str, Any]]
) -> int:
    """Thêm hợp đồng còn thiếu theo tên gói, không tạo trùng khi chạy lại."""
    existing_names = set(
        (
            await session.execute(
                select(Contract.package_name).where(Contract.project_id == project_id)
            )
        ).scalars()
    )
    inserted = 0
    for row in rows:
        if row["package_name"] in existing_names:
            continue
        await create_contract(
            session,
            project_id=project_id,
            payload=ContractCreate.model_validate(row),
        )
        inserted += 1
    return inserted


async def seed_hcm_project(session_factory: async_sessionmaker[AsyncSession]) -> int:
    """Nạp SGD-HCM gồm đơn vị, mốc và hợp đồng trong một transaction; trả về số đơn vị mới."""
    async with session_factory() as session:
        project = await ensure_project(session, HCM_PROJECT)
        inserted = await ensure_units(session, project.id, load_units(HCM_UNITS_FILE))
        milestones = await ensure_milestones(
            session, project.id, load_seed_rows(HCM_MILESTONES_FILE)
        )
        contracts = await ensure_contracts(session, project.id, load_seed_rows(HCM_CONTRACTS_FILE))
        risks = await ensure_risks(session, project, load_seed_rows(HCM_RISKS_FILE))
        await session.commit()
    logger.info("Seed %s: thêm %d rủi ro", HCM_PROJECT.code, risks)
    logger.info("Seed %s: thêm %d hợp đồng", HCM_PROJECT.code, contracts)
    logger.info("Seed %s: thêm %d đơn vị thụ hưởng, %d mốc", HCM_PROJECT.code, inserted, milestones)
    return inserted


async def seed_lam_dong_project(session_factory: async_sessionmaker[AsyncSession]) -> int:
    """Nạp SGD-LD gồm 62 đơn vị và gói thầu chính trong một transaction; trả về số đơn vị mới."""
    async with session_factory() as session:
        project = await ensure_project(session, LAM_DONG_PROJECT)
        inserted = await ensure_units(session, project.id, load_units(LAM_DONG_UNITS_FILE))
        contracts = await ensure_contracts(
            session, project.id, load_seed_rows(LAM_DONG_CONTRACTS_FILE)
        )
        milestones = await ensure_milestones(
            session, project.id, load_seed_rows(LAM_DONG_MILESTONES_FILE)
        )
        risks = await ensure_risks(session, project, load_seed_rows(LAM_DONG_RISKS_FILE))
        await session.commit()
    logger.info("Seed %s: thêm %d mốc, %d rủi ro", LAM_DONG_PROJECT.code, milestones, risks)
    logger.info("Seed %s: thêm %d hợp đồng", LAM_DONG_PROJECT.code, contracts)
    logger.info("Seed %s: thêm %d đơn vị thụ hưởng", LAM_DONG_PROJECT.code, inserted)
    return inserted


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)

    async def _run() -> None:
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            await seed_hcm_project(session_factory)
            await seed_lam_dong_project(session_factory)
        finally:
            await engine.dispose()

    asyncio.run(_run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
