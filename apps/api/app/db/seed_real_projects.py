"""Nạp dữ liệu thật của dự án theo spec §7. Chạy lại an toàn: bản ghi đã có được bỏ qua."""

import asyncio
import json
import logging
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.contract import Contract
from app.models.legal_document import DocMaturityStatus, LegalDocument
from app.models.milestone import Milestone, StoredMilestoneStatus
from app.models.project import Project, ProjectArchetype
from app.models.project_budget_item import ProjectBudgetItem
from app.models.project_file_register import ProjectFileRegisterEntry
from app.models.project_legal_decision import ProjectLegalDecision
from app.models.risk_issue import RiskIssue
from app.schemas.beneficiary_units import BeneficiaryUnitCreate
from app.schemas.contracts import ContractCreate
from app.schemas.file_register import FileRegisterCreate
from app.schemas.legal_documents import LegalDocumentCreate
from app.schemas.milestones import MilestoneCreate
from app.schemas.project_budget_items import ProjectBudgetItemCreate
from app.schemas.project_legal_decisions import ProjectLegalDecisionCreate
from app.schemas.projects import ProjectCreate
from app.schemas.risk_issues import RiskIssueCreate
from app.services.audit import record_audit
from app.services.beneficiary_units import create_unit, find_unit_by_code
from app.services.contracts import create_contract
from app.services.file_register import create_file_entry
from app.services.legal_documents import create_legal_document
from app.services.milestones import create_milestone, find_milestone_by_code
from app.services.projects import create_project
from app.services.risk_issues import create_risk_issue

logger = logging.getLogger(__name__)

SEED_DATA_DIR = Path(__file__).resolve().parent / "seed_data"
HCM_UNITS_FILE = SEED_DATA_DIR / "hcm_survey_units.json"
HCM_MILESTONES_FILE = SEED_DATA_DIR / "hcm_milestones.json"
HCM_CONTRACTS_FILE = SEED_DATA_DIR / "hcm_contracts.json"
HCM_RISKS_FILE = SEED_DATA_DIR / "hcm_risks.json"
HCM_LEGAL_DOCUMENTS_FILE = SEED_DATA_DIR / "hcm_legal_documents.json"
LAM_DONG_UNITS_FILE = SEED_DATA_DIR / "lam_dong_units.json"
LAM_DONG_CONTRACTS_FILE = SEED_DATA_DIR / "lam_dong_contracts.json"
LAM_DONG_MILESTONES_FILE = SEED_DATA_DIR / "lam_dong_milestones.json"
LAM_DONG_RISKS_FILE = SEED_DATA_DIR / "lam_dong_risks.json"
LAM_DONG_LEGAL_DOCUMENTS_FILE = SEED_DATA_DIR / "lam_dong_legal_documents.json"
HCM_FILE_REGISTER_FILE = SEED_DATA_DIR / "hcm_file_register.json"
LAM_DONG_FILE_REGISTER_FILE = SEED_DATA_DIR / "lam_dong_file_register.json"
HCM_LEGAL_DECISIONS_FILE = SEED_DATA_DIR / "hcm_legal_decisions.json"
HCM_BUDGET_ITEMS_FILE = SEED_DATA_DIR / "hcm_budget_items.json"
LAM_DONG_LEGAL_DECISIONS_FILE = SEED_DATA_DIR / "lam_dong_legal_decisions.json"

HCM_PROJECT = ProjectCreate(
    code="SGD-HCM-CSVC-2026",
    name="Xây dựng hệ thống quản lý dữ liệu về cơ sở vật chất và thiết bị trường học",
    short_name="SGD-HCM CSVC 2026",
    archetype=ProjectArchetype.IT_SYSTEM,
    investor_name="Sở GD&ĐT TP.HCM",
    decision_authority="Ủy ban nhân dân Thành phố Hồ Chí Minh",
    legal_representative="Ông Nguyễn Văn Hiếu — Giám đốc Sở GD&ĐT",
    qlda_form="Chủ đầu tư thuê tư vấn quản lý dự án (Công ty Sài Gòn Mới)",
    disbursement_deadline="09/12/2026 (Hạn chót giải ngân niên độ tài chính năm 2026)",
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


PROJECT_FILLABLE_FIELDS = (
    "decision_authority",
    "legal_representative",
    "qlda_form",
    "disbursement_deadline",
)


def _fill_empty_project_fields(project: Project, payload: ProjectCreate) -> None:
    """Điền trường còn trống của dự án đã có từ seed; không ghi đè giá trị đã nhập."""
    for field in PROJECT_FILLABLE_FIELDS:
        value = getattr(payload, field)
        if getattr(project, field) is None and value is not None:
            setattr(project, field, value)


async def ensure_project(session: AsyncSession, payload: ProjectCreate) -> Project:
    existing = await find_project_by_code(session, payload.code)
    if existing is not None:
        _fill_empty_project_fields(existing, payload)
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


SEED_OWNED_MILESTONE_TEXT_FIELDS = (
    "name",
    "deliverables",
    "acceptance_conditions",
    "tvgs_checkpoint",
    "pm_comment",
)


def _refresh_seed_text(milestone: Milestone, payload: MilestoneCreate) -> bool:
    """Ghi đè các trường chữ nguồn từ Excel/Drive lên bản seed cũ; trả về True nếu có đổi."""
    changed = False
    values = payload.model_dump()
    for field in SEED_OWNED_MILESTONE_TEXT_FIELDS:
        if values[field] is not None and getattr(milestone, field) != values[field]:
            setattr(milestone, field, values[field])
            changed = True
    return changed


class MilestoneSeedRow(MilestoneCreate):
    """Dòng mốc nạp seed: kèm trạng thái và ngày hoàn thành đã đối chiếu từ báo cáo tracking."""

    status: StoredMilestoneStatus = StoredMilestoneStatus.NOT_STARTED
    actual_end: date | None = None


async def ensure_milestones(
    session: AsyncSession, project_id: UUID, rows: list[dict[str, Any]]
) -> int:
    inserted = 0
    for row in rows:
        payload = MilestoneSeedRow(**row)
        existing = await find_milestone_by_code(session, project_id, payload.code)
        if existing is not None:
            if _refresh_seed_text(existing, payload):
                await session.flush()
            continue
        milestone = await create_milestone(
            session,
            project_id=project_id,
            values=payload.model_dump(exclude={"status", "actual_end"}),
        )
        milestone.status = payload.status
        milestone.actual_end = payload.actual_end
        await session.flush()
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


CONTRACT_FILLABLE_FIELDS = (
    "contract_number",
    "signed_date",
    "expiration_date",
    "role_label",
    "contractor_name",
    "contact_person",
    "status_note",
)


def _fill_empty_contract_fields(contract: Contract, payload: ContractCreate) -> None:
    """Điền trường còn trống từ seed; không ghi đè giá trị đã có trong DB."""
    for field in CONTRACT_FILLABLE_FIELDS:
        value = getattr(payload, field)
        if getattr(contract, field) is None and value is not None:
            setattr(contract, field, value)


async def ensure_contracts(
    session: AsyncSession, project_id: UUID, rows: list[dict[str, Any]]
) -> int:
    """Thêm hợp đồng còn thiếu theo tên gói và điền trường còn trống của hợp đồng đã có."""
    existing_by_name = {
        contract.package_name: contract
        for contract in (
            await session.execute(select(Contract).where(Contract.project_id == project_id))
        ).scalars()
    }
    inserted = 0
    for row in rows:
        payload = ContractCreate.model_validate(row)
        existing = existing_by_name.get(payload.package_name)
        if existing is not None:
            _fill_empty_contract_fields(existing, payload)
            continue
        await create_contract(session, project_id=project_id, payload=payload)
        inserted += 1
    return inserted


async def ensure_budget_items(
    session: AsyncSession, project_id: UUID, rows: list[dict[str, Any]]
) -> int:
    """Thêm khoản chi còn thiếu theo nhóm, không tạo trùng khi chạy lại."""
    existing_categories = set(
        (
            await session.execute(
                select(ProjectBudgetItem.category).where(ProjectBudgetItem.project_id == project_id)
            )
        ).scalars()
    )
    inserted = 0
    for row in rows:
        payload = ProjectBudgetItemCreate(**row)
        if payload.category in existing_categories:
            continue
        session.add(ProjectBudgetItem(project_id=project_id, **payload.model_dump()))
        inserted += 1
    await session.flush()
    return inserted


class LegalDocumentSeedRow(LegalDocumentCreate):
    """Dòng seed hồ sơ pháp lý; khác API tạo mới ở chỗ được nạp kèm trạng thái đã đối chiếu."""

    maturity_status: DocMaturityStatus = DocMaturityStatus.MISSING


async def ensure_legal_documents(
    session: AsyncSession, project_id: UUID, rows: list[dict[str, Any]]
) -> int:
    """Thêm hồ sơ pháp lý còn thiếu theo `stt`, không tạo trùng khi chạy lại."""
    existing_stts = set(
        (
            await session.execute(
                select(LegalDocument.stt).where(LegalDocument.project_id == project_id)
            )
        ).scalars()
    )
    inserted = 0
    for row in rows:
        payload = LegalDocumentSeedRow(**row)
        if payload.stt in existing_stts:
            continue
        document = await create_legal_document(
            session,
            project_id=project_id,
            values=payload.model_dump(),
        )
        await record_audit(
            session,
            actor_id=None,
            action="legal_document.seed",
            entity_type="legal_document",
            entity_id=str(document.id),
            changes={"stt": document.stt},
        )
        inserted += 1
    return inserted


async def ensure_file_register(
    session: AsyncSession, project_id: UUID, rows: list[dict[str, Any]]
) -> int:
    """Thêm dòng file register còn thiếu theo `stt`, không tạo trùng khi chạy lại."""
    existing_stts = set(
        (
            await session.execute(
                select(ProjectFileRegisterEntry.stt).where(
                    ProjectFileRegisterEntry.project_id == project_id
                )
            )
        ).scalars()
    )
    inserted = 0
    for row in rows:
        payload = FileRegisterCreate(**row)
        if payload.stt in existing_stts:
            continue
        entry = await create_file_entry(
            session,
            project_id=project_id,
            values=payload.model_dump(),
        )
        await record_audit(
            session,
            actor_id=None,
            action="file_register.seed",
            entity_type="file_register",
            entity_id=str(entry.id),
            changes={"stt": entry.stt},
        )
        inserted += 1
    return inserted


async def ensure_legal_decisions(
    session: AsyncSession, project_id: UUID, rows: list[dict[str, Any]]
) -> int:
    """Thêm quyết định còn thiếu theo số hiệu, không tạo trùng khi chạy lại."""
    existing_numbers = set(
        (
            await session.execute(
                select(ProjectLegalDecision.decision_no).where(
                    ProjectLegalDecision.project_id == project_id
                )
            )
        ).scalars()
    )
    inserted = 0
    for row in rows:
        payload = ProjectLegalDecisionCreate(**row)
        if payload.decision_no in existing_numbers:
            continue
        decision = ProjectLegalDecision(project_id=project_id, **payload.model_dump())
        session.add(decision)
        await session.flush()
        await record_audit(
            session,
            actor_id=None,
            action="project_legal_decision.seed",
            entity_type="project_legal_decision",
            entity_id=str(decision.id),
            changes={"decision_no": decision.decision_no},
        )
        inserted += 1
    return inserted


async def seed_hcm_project(session_factory: async_sessionmaker[AsyncSession]) -> int:
    """Nạp SGD-HCM (đơn vị, mốc, hợp đồng, rủi ro, hồ sơ pháp lý) trong một transaction."""
    async with session_factory() as session:
        project = await ensure_project(session, HCM_PROJECT)
        inserted = await ensure_units(session, project.id, load_units(HCM_UNITS_FILE))
        milestones = await ensure_milestones(
            session, project.id, load_seed_rows(HCM_MILESTONES_FILE)
        )
        contracts = await ensure_contracts(session, project.id, load_seed_rows(HCM_CONTRACTS_FILE))
        risks = await ensure_risks(session, project, load_seed_rows(HCM_RISKS_FILE))
        legal_documents = await ensure_legal_documents(
            session, project.id, load_seed_rows(HCM_LEGAL_DOCUMENTS_FILE)
        )
        file_entries = await ensure_file_register(
            session, project.id, load_seed_rows(HCM_FILE_REGISTER_FILE)
        )
        decisions = await ensure_legal_decisions(
            session, project.id, load_seed_rows(HCM_LEGAL_DECISIONS_FILE)
        )
        budget_items = await ensure_budget_items(
            session, project.id, load_seed_rows(HCM_BUDGET_ITEMS_FILE)
        )
        await session.commit()
    logger.info("Seed %s: thêm %d khoản chi", HCM_PROJECT.code, budget_items)
    logger.info("Seed %s: thêm %d quyết định pháp lý", HCM_PROJECT.code, decisions)
    logger.info("Seed %s: thêm %d dòng file register", HCM_PROJECT.code, file_entries)
    logger.info("Seed %s: thêm %d hồ sơ pháp lý", HCM_PROJECT.code, legal_documents)
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
        legal_documents = await ensure_legal_documents(
            session, project.id, load_seed_rows(LAM_DONG_LEGAL_DOCUMENTS_FILE)
        )
        file_entries = await ensure_file_register(
            session, project.id, load_seed_rows(LAM_DONG_FILE_REGISTER_FILE)
        )
        decisions = await ensure_legal_decisions(
            session, project.id, load_seed_rows(LAM_DONG_LEGAL_DECISIONS_FILE)
        )
        await session.commit()
    logger.info("Seed %s: thêm %d quyết định pháp lý", LAM_DONG_PROJECT.code, decisions)
    logger.info("Seed %s: thêm %d dòng file register", LAM_DONG_PROJECT.code, file_entries)
    logger.info("Seed %s: thêm %d hồ sơ pháp lý", LAM_DONG_PROJECT.code, legal_documents)
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
