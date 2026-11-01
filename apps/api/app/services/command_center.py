"""Tổng hợp Command Center: chỉ đọc, gom bằng số truy vấn cố định (không N+1).

Phạm vi dự án do `list_projects` quyết định (ADMIN thấy tất cả, còn lại theo thành viên).
Mọi truy vấn sau đó lọc theo danh sách id dự án đó, nên dữ liệu không rò rỉ giữa các dự án.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.command_center_rules import (
    MilestoneTiming,
    build_health_inputs,
    is_red_milestone,
    sum_contract_values_by_kind,
)
from app.core.contract_countdown import CountdownStatus, countdown_status
from app.core.project_health import DEFAULT_HEALTH_THRESHOLDS, derive_project_health
from app.core.red_alert_rules import is_red_alert
from app.core.schedule_rules import effective_due_date
from app.models.beneficiary_unit import BeneficiaryUnit
from app.models.contract import Contract
from app.models.milestone import Milestone
from app.models.project import Project, ProjectHealth
from app.models.risk_issue import RiskIssue, RiskStatus
from app.schemas.command_center import (
    CommandCenterKpi,
    CommandCenterOut,
    ContractCountdownRow,
    ProjectHealthRow,
    RedAlertRow,
)
from app.services.projects import list_projects

CLOSED_RISK_STATUSES = (RiskStatus.RESOLVED, RiskStatus.CLOSED)
COUNTDOWN_STATUSES_TO_SHOW = (CountdownStatus.WARNING, CountdownStatus.EXPIRED)


@dataclass(frozen=True)
class _MilestoneRow:
    code: str
    name: str
    timing: MilestoneTiming


@dataclass(frozen=True)
class _RiskRow:
    code: str
    title: str
    due_date: date


@dataclass(frozen=True)
class _ContractRow:
    project_id: UUID
    contract_number: str | None
    package_kind: str
    contract_value: Decimal
    expiration_date: date | None


async def _load_milestones(
    session: AsyncSession, project_ids: list[UUID]
) -> dict[UUID, list[_MilestoneRow]]:
    query = select(
        Milestone.project_id,
        Milestone.code,
        Milestone.name,
        Milestone.baseline_end,
        Milestone.adjusted_end,
        Milestone.actual_end,
        Milestone.is_hard_deadline,
    ).where(Milestone.project_id.in_(project_ids))
    grouped: dict[UUID, list[_MilestoneRow]] = defaultdict(list)
    for row in (await session.execute(query)).all():
        timing = MilestoneTiming(
            baseline_end=row.baseline_end,
            adjusted_end=row.adjusted_end,
            actual_end=row.actual_end,
            is_hard_deadline=row.is_hard_deadline,
        )
        grouped[row.project_id].append(_MilestoneRow(code=row.code, name=row.name, timing=timing))
    return dict(grouped)


async def _load_open_risks(
    session: AsyncSession, project_ids: list[UUID]
) -> dict[UUID, list[_RiskRow]]:
    query = (
        select(RiskIssue.project_id, RiskIssue.code, RiskIssue.title, RiskIssue.due_date)
        .where(RiskIssue.project_id.in_(project_ids))
        .where(RiskIssue.due_date.is_not(None))
        .where(RiskIssue.status.not_in(CLOSED_RISK_STATUSES))
    )
    grouped: dict[UUID, list[_RiskRow]] = defaultdict(list)
    for row in (await session.execute(query)).all():
        grouped[row.project_id].append(
            _RiskRow(code=row.code, title=row.title, due_date=row.due_date)
        )
    return dict(grouped)


async def _load_contracts(session: AsyncSession, project_ids: list[UUID]) -> list[_ContractRow]:
    query = select(
        Contract.project_id,
        Contract.contract_number,
        Contract.package_kind,
        Contract.contract_value,
        Contract.expiration_date,
    ).where(Contract.project_id.in_(project_ids))
    rows = (await session.execute(query)).all()
    return [
        _ContractRow(
            project_id=row.project_id,
            contract_number=row.contract_number,
            package_kind=row.package_kind,
            contract_value=row.contract_value,
            expiration_date=row.expiration_date,
        )
        for row in rows
    ]


async def _load_unit_counts(session: AsyncSession, project_ids: list[UUID]) -> dict[UUID, int]:
    query = (
        select(BeneficiaryUnit.project_id, func.count(BeneficiaryUnit.id))
        .where(BeneficiaryUnit.project_id.in_(project_ids))
        .group_by(BeneficiaryUnit.project_id)
    )
    return {row[0]: row[1] for row in (await session.execute(query)).all()}


def _project_summary(
    project: Project,
    milestones: list[_MilestoneRow],
    risks: list[_RiskRow],
    today: date,
) -> tuple[ProjectHealthRow, list[RedAlertRow]]:
    red_alerts = [
        RedAlertRow(
            project_code=project.code,
            source="MILESTONE",
            code=row.code,
            title=row.name,
            due_date=effective_due_date(row.timing.baseline_end, row.timing.adjusted_end),
        )
        for row in milestones
        if is_red_milestone(row.timing, today)
    ]
    red_alerts += [
        RedAlertRow(
            project_code=project.code,
            source="RISK",
            code=risk.code,
            title=risk.title,
            due_date=risk.due_date,
        )
        for risk in risks
        if is_red_alert(risk.due_date, today)
    ]
    inputs = build_health_inputs(
        [row.timing for row in milestones],
        red_alert_count=len(red_alerts),
        is_completed=project.health_status == ProjectHealth.COMPLETED,
        today=today,
    )
    summary = ProjectHealthRow(
        id=project.id,
        code=project.code,
        short_name=project.short_name,
        health=derive_project_health(inputs, DEFAULT_HEALTH_THRESHOLDS),
        red_alert_count=len(red_alerts),
        max_slippage_days=inputs.max_slippage_days,
    )
    return summary, red_alerts


def _countdown_rows(
    contracts: list[_ContractRow],
    project_codes: dict[UUID, str],
    today: date,
) -> list[ContractCountdownRow]:
    rows: list[ContractCountdownRow] = []
    for contract in contracts:
        if contract.expiration_date is None:
            continue
        status = countdown_status(contract.expiration_date, today)
        if status not in COUNTDOWN_STATUSES_TO_SHOW:
            continue
        rows.append(
            ContractCountdownRow(
                project_code=project_codes[contract.project_id],
                contract_number=contract.contract_number,
                status=status,
                expiration_date=contract.expiration_date,
                days_remaining=(contract.expiration_date - today).days,
            )
        )
    return sorted(rows, key=lambda row: row.expiration_date)


async def build_command_center(
    session: AsyncSession,
    *,
    today: date,
    member_user_id: UUID | None,
) -> CommandCenterOut:
    """Gom KPI, sức khỏe, thẻ đỏ và đếm ngược hợp đồng cho các dự án người xem được."""
    projects = await list_projects(session, member_user_id=member_user_id)
    project_ids = [project.id for project in projects]
    milestones = await _load_milestones(session, project_ids)
    risks = await _load_open_risks(session, project_ids)
    contracts = await _load_contracts(session, project_ids)
    unit_counts = await _load_unit_counts(session, project_ids)

    summaries: list[ProjectHealthRow] = []
    red_alerts: list[RedAlertRow] = []
    for project in projects:
        summary, project_red_alerts = _project_summary(
            project, milestones.get(project.id, []), risks.get(project.id, []), today
        )
        summaries.append(summary)
        red_alerts += project_red_alerts

    by_kind = sum_contract_values_by_kind(
        (contract.package_kind, contract.contract_value) for contract in contracts
    )
    kpi = CommandCenterKpi(
        contract_value_by_kind=by_kind,
        contract_value_total=sum(by_kind.values(), Decimal("0")),
        running_project_count=sum(
            1 for summary in summaries if summary.health != ProjectHealth.COMPLETED
        ),
        beneficiary_unit_count=sum(unit_counts.values()),
        red_alert_count=len(red_alerts),
    )
    project_codes = {project.id: project.code for project in projects}
    return CommandCenterOut(
        as_of=today,
        kpi=kpi,
        projects=summaries,
        red_alerts=sorted(red_alerts, key=lambda row: row.due_date),
        contract_countdowns=_countdown_rows(contracts, project_codes, today),
    )
