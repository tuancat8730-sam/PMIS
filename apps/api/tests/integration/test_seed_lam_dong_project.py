import pytest
from fastapi import FastAPI
from sqlalchemy import func, select

from app.db.seed_real_projects import seed_lam_dong_project
from app.models.beneficiary_unit import BeneficiaryUnit
from app.models.contract import Contract
from app.models.milestone import Milestone
from app.models.project import Project
from app.models.risk_issue import RiskIssue

pytestmark = pytest.mark.integration

LAM_DONG_UNIT_COUNT = 62
LAM_DONG_MILESTONE_COUNT = 5
LAM_DONG_RISK_COUNT = 8


async def test_seed_creates_lam_dong_project_62_units_and_main_contract_once(
    app: FastAPI,
) -> None:
    # Arrange
    session_factory = app.state.session_factory

    # Act
    inserted = await seed_lam_dong_project(session_factory)

    # Assert
    assert inserted == LAM_DONG_UNIT_COUNT
    async with session_factory() as session:
        project_count = await session.scalar(select(func.count()).select_from(Project))
        unit_count = await session.scalar(select(func.count()).select_from(BeneficiaryUnit))
        contract_count = await session.scalar(select(func.count()).select_from(Contract))
    assert project_count == 1
    assert unit_count == LAM_DONG_UNIT_COUNT
    assert contract_count == 1


async def test_running_lam_dong_seed_twice_does_not_duplicate_records(app: FastAPI) -> None:
    # Arrange
    session_factory = app.state.session_factory
    await seed_lam_dong_project(session_factory)

    # Act
    second_run_inserted = await seed_lam_dong_project(session_factory)

    # Assert
    assert second_run_inserted == 0
    async with session_factory() as session:
        project_count = await session.scalar(select(func.count()).select_from(Project))
        unit_count = await session.scalar(select(func.count()).select_from(BeneficiaryUnit))
        contract_count = await session.scalar(select(func.count()).select_from(Contract))
    assert project_count == 1
    assert unit_count == LAM_DONG_UNIT_COUNT
    assert contract_count == 1


async def test_seed_creates_lam_dong_milestones_and_risks_without_unrated_levels(
    app: FastAPI,
) -> None:
    # Arrange
    session_factory = app.state.session_factory

    # Act
    await seed_lam_dong_project(session_factory)
    await seed_lam_dong_project(session_factory)

    # Assert
    async with session_factory() as session:
        milestone_count = await session.scalar(select(func.count()).select_from(Milestone))
        risks = (await session.execute(select(RiskIssue))).scalars().all()
    assert milestone_count == LAM_DONG_MILESTONE_COUNT
    assert len(risks) == LAM_DONG_RISK_COUNT
    assert all(risk.impact is None and risk.likelihood is None for risk in risks)
