import pytest
from fastapi import FastAPI
from sqlalchemy import func, select

from app.db.seed_real_projects import seed_hcm_project
from app.models.audit_log import AuditLog
from app.models.beneficiary_unit import BeneficiaryUnit
from app.models.milestone import Milestone
from app.models.project import Project
from app.models.risk_issue import RiskIssue, RiskLevel

pytestmark = pytest.mark.integration

HCM_UNIT_COUNT = 8
HCM_MILESTONE_CODES = {"H0", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9"}
HCM_RISK_COUNT = 12


async def test_seed_creates_known_hcm_milestones_with_hard_deadlines(app: FastAPI) -> None:
    # Arrange
    session_factory = app.state.session_factory

    # Act
    await seed_hcm_project(session_factory)

    # Assert
    async with session_factory() as session:
        milestones = (await session.execute(select(Milestone))).scalars().all()
    by_code = {milestone.code: milestone for milestone in milestones}
    assert set(by_code) == HCM_MILESTONE_CODES
    assert by_code["M8"].is_hard_deadline is True
    assert by_code["M9"].is_hard_deadline is True
    assert by_code["M1"].is_hard_deadline is False
    assert str(by_code["M8"].baseline_end) == "2026-11-30"
    assert str(by_code["M9"].baseline_end) == "2026-12-09"


async def test_running_seed_twice_does_not_duplicate_milestones(app: FastAPI) -> None:
    # Arrange
    session_factory = app.state.session_factory
    await seed_hcm_project(session_factory)

    # Act
    await seed_hcm_project(session_factory)

    # Assert
    async with session_factory() as session:
        milestone_count = await session.scalar(select(func.count()).select_from(Milestone))
    assert milestone_count == len(HCM_MILESTONE_CODES)


async def test_seed_creates_hcm_project_and_eight_units_once(app: FastAPI) -> None:
    # Arrange
    session_factory = app.state.session_factory

    # Act
    inserted = await seed_hcm_project(session_factory)

    # Assert
    assert inserted == HCM_UNIT_COUNT
    async with session_factory() as session:
        project_count = await session.scalar(select(func.count()).select_from(Project))
        unit_count = await session.scalar(select(func.count()).select_from(BeneficiaryUnit))
    assert project_count == 1
    assert unit_count == HCM_UNIT_COUNT


async def test_running_seed_twice_does_not_duplicate_records(app: FastAPI) -> None:
    # Arrange
    session_factory = app.state.session_factory
    await seed_hcm_project(session_factory)

    # Act
    second_run_inserted = await seed_hcm_project(session_factory)

    # Assert
    assert second_run_inserted == 0
    async with session_factory() as session:
        unit_count = await session.scalar(select(func.count()).select_from(BeneficiaryUnit))
        seed_audit_count = await session.scalar(
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.action == "beneficiary_unit.seed")
        )
    assert unit_count == HCM_UNIT_COUNT
    assert seed_audit_count == HCM_UNIT_COUNT


async def test_seed_writes_audit_without_actor(app: FastAPI) -> None:
    # Arrange
    session_factory = app.state.session_factory

    # Act
    await seed_hcm_project(session_factory)

    # Assert
    async with session_factory() as session:
        actors = (
            (
                await session.execute(
                    select(AuditLog.actor_id).where(AuditLog.action == "project.seed")
                )
            )
            .scalars()
            .all()
        )
    assert actors == [None]


async def test_seed_creates_hcm_risks_with_levels_and_runs_idempotently(app: FastAPI) -> None:
    # Arrange
    session_factory = app.state.session_factory

    # Act
    await seed_hcm_project(session_factory)
    await seed_hcm_project(session_factory)

    # Assert
    async with session_factory() as session:
        risks = (await session.execute(select(RiskIssue))).scalars().all()
    assert len(risks) == HCM_RISK_COUNT
    r01 = next(risk for risk in risks if risk.title.endswith("(R01)"))
    assert r01.impact == RiskLevel.VERY_HIGH
    assert r01.likelihood == RiskLevel.VERY_HIGH
