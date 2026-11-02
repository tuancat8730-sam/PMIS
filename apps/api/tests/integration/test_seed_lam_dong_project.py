import pytest
from fastapi import FastAPI
from sqlalchemy import func, select

from app.db.seed_real_projects import seed_lam_dong_project
from app.models.beneficiary_unit import BeneficiaryUnit
from app.models.contract import Contract
from app.models.project import Project

pytestmark = pytest.mark.integration

LAM_DONG_UNIT_COUNT = 62


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
