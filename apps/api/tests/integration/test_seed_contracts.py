from decimal import Decimal

import pytest
from fastapi import FastAPI
from sqlalchemy import func, select

from app.db.seed_real_projects import HCM_PROJECT, seed_hcm_project
from app.models.contract import Contract
from app.models.project import Project

pytestmark = pytest.mark.integration

# Giá trị lấy từ PROJECT_MANAGEMENT_SOFTWARE_SPEC.md mục 7, dự án SGD-HCM-CSVC-2026.
EXPECTED_HCM_CONTRACTS = {
    "Gói thầu chính": ("MAIN", Decimal("4848186000.00")),
    "Gói TVGS": ("CONSULTING", Decimal("120000000.00")),
    "Gói TVQLDA": ("CONSULTING", Decimal("109000000.00")),
}


async def _hcm_contracts(app: FastAPI) -> dict[str, tuple[str, Decimal]]:
    session_factory = app.state.session_factory
    async with session_factory() as session:
        project_id = (
            await session.execute(select(Project.id).where(Project.code == HCM_PROJECT.code))
        ).scalar_one()
        rows = (
            await session.execute(select(Contract).where(Contract.project_id == project_id))
        ).scalars()
        return {row.package_name: (row.package_kind, row.contract_value) for row in rows}


async def test_seed_contracts_match_spec_section_7_values(app: FastAPI) -> None:
    # Arrange
    session_factory = app.state.session_factory

    # Act
    await seed_hcm_project(session_factory)

    # Assert
    assert await _hcm_contracts(app) == EXPECTED_HCM_CONTRACTS


async def test_seed_contracts_are_not_duplicated_when_run_again(app: FastAPI) -> None:
    # Arrange
    session_factory = app.state.session_factory
    await seed_hcm_project(session_factory)

    # Act
    await seed_hcm_project(session_factory)

    # Assert
    async with session_factory() as session:
        count = (await session.execute(select(func.count()).select_from(Contract))).scalar_one()
    assert count == len(EXPECTED_HCM_CONTRACTS)
