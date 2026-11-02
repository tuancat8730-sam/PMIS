import pytest

from app.db.seed_real_projects import (
    LAM_DONG_CONTRACTS_FILE,
    LAM_DONG_PROJECT,
    load_seed_rows,
)
from app.models.project import ProjectArchetype
from app.schemas.contracts import ContractCreate

pytestmark = pytest.mark.unit

LAM_DONG_CONTRACT_NUMBER = "HD2600226555_2609110905"


def test_lam_dong_project_uses_plan_code_and_goods_archetype() -> None:
    # Arrange
    expected_code = "SGD-LD-TB10-2026"

    # Act
    project = LAM_DONG_PROJECT

    # Assert
    assert project.code == expected_code
    assert project.archetype == ProjectArchetype.GOODS_PROCUREMENT


def test_lam_dong_contract_file_has_one_main_package_with_contract_number() -> None:
    # Arrange
    rows = load_seed_rows(LAM_DONG_CONTRACTS_FILE)

    # Act
    contracts = [ContractCreate.model_validate(row) for row in rows]

    # Assert
    assert len(contracts) == 1
    assert contracts[0].package_kind == "MAIN"
    assert contracts[0].contract_number == LAM_DONG_CONTRACT_NUMBER


def test_lam_dong_total_investment_equals_main_contract_value_until_tmdt_is_confirmed() -> None:
    # Arrange
    contract = ContractCreate.model_validate(load_seed_rows(LAM_DONG_CONTRACTS_FILE)[0])

    # Act
    total_investment = LAM_DONG_PROJECT.total_investment

    # Assert
    assert total_investment == contract.contract_value
