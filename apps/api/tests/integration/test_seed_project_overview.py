from datetime import date
from decimal import Decimal

import pytest
from fastapi import FastAPI
from sqlalchemy import select

from app.db.seed_real_projects import seed_hcm_project
from app.models.contract import Contract
from app.models.project import Project
from app.models.project_budget_item import BudgetCategory, ProjectBudgetItem

pytestmark = pytest.mark.integration

HCM_CODE = "SGD-HCM-CSVC-2026"
HCM_AUTHORITY = "Ủy ban nhân dân Thành phố Hồ Chí Minh"
HCM_BUDGET_ITEM_COUNT = 5
HCM_CONTRACT_COUNT = 7
HCM_LEGAL_REPRESENTATIVE = "Ông Nguyễn Văn Hiếu — Giám đốc Sở GD&ĐT"
HCM_QLDA_FORM = "Chủ đầu tư thuê tư vấn quản lý dự án (Công ty Sài Gòn Mới)"
HCM_DISBURSEMENT_DEADLINE = "09/12/2026 (Hạn chót giải ngân niên độ tài chính năm 2026)"


async def _hcm_project_id(app: FastAPI) -> object:
    async with app.state.session_factory() as session:
        return (
            await session.execute(select(Project.id).where(Project.code == HCM_CODE))
        ).scalar_one()


async def test_seed_hcm_budget_items_and_authority_idempotent(app: FastAPI) -> None:
    # Arrange
    session_factory = app.state.session_factory

    # Act
    await seed_hcm_project(session_factory)
    await seed_hcm_project(session_factory)

    # Assert
    project_id = await _hcm_project_id(app)
    async with session_factory() as session:
        items = (
            (
                await session.execute(
                    select(ProjectBudgetItem).where(ProjectBudgetItem.project_id == project_id)
                )
            )
            .scalars()
            .all()
        )
        project = (
            await session.execute(select(Project).where(Project.code == HCM_CODE))
        ).scalar_one()
    by_category = {item.category: item for item in items}
    assert len(items) == HCM_BUDGET_ITEM_COUNT
    assert by_category[BudgetCategory.SOFTWARE].amount == Decimal("5447400000.00")
    assert by_category[BudgetCategory.CONTINGENCY].amount == Decimal("0")
    assert project.decision_authority == HCM_AUTHORITY


async def test_seed_hcm_consulting_contracts_fill_numbers_and_dates_from_image(
    app: FastAPI,
) -> None:
    # Arrange
    session_factory = app.state.session_factory

    # Act
    await seed_hcm_project(session_factory)

    # Assert
    project_id = await _hcm_project_id(app)
    async with session_factory() as session:
        contracts = (
            (await session.execute(select(Contract).where(Contract.project_id == project_id)))
            .scalars()
            .all()
        )
    by_name = {contract.package_name: contract for contract in contracts}
    assert len(contracts) == HCM_CONTRACT_COUNT
    tvgs = by_name["Gói TVGS"]
    assert tvgs.contract_number == "24.8.26/HĐTV/SGDĐT-CRYSTAL"
    assert tvgs.signed_date == date(2026, 8, 24)
    assert tvgs.expiration_date == date(2027, 1, 21)
    tvqlda = by_name["Gói TVQLDA"]
    assert tvqlda.contract_number == "248/HĐKT-QLDA"
    assert tvqlda.signed_date == date(2026, 8, 24)
    assert tvqlda.contract_value == Decimal("109000000.00")


async def test_seed_hcm_project_overview_fields_from_image(app: FastAPI) -> None:
    # Arrange
    session_factory = app.state.session_factory

    # Act
    await seed_hcm_project(session_factory)

    # Assert
    async with session_factory() as session:
        project = (
            await session.execute(select(Project).where(Project.code == HCM_CODE))
        ).scalar_one()
    assert project.legal_representative == HCM_LEGAL_REPRESENTATIVE
    assert project.qlda_form == HCM_QLDA_FORM
    assert project.disbursement_deadline == HCM_DISBURSEMENT_DEADLINE
