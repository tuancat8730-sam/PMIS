import pytest
from pydantic import ValidationError

from app.schemas.contracts import ContractCreate

pytestmark = pytest.mark.unit

BASE_FIELDS = {"package_name": "Gói tư vấn TVGS", "contract_value": "1000000.00"}


def test_contract_package_kind_defaults_to_main_package() -> None:
    # Act
    contract = ContractCreate(**BASE_FIELDS)

    # Assert
    assert contract.package_kind == "MAIN"


def test_consulting_package_kind_is_accepted() -> None:
    # Act
    contract = ContractCreate(**BASE_FIELDS, package_kind="CONSULTING")

    # Assert
    assert contract.package_kind == "CONSULTING"


def test_unknown_package_kind_fails_validation() -> None:
    # Act / Assert
    with pytest.raises(ValidationError):
        ContractCreate(**BASE_FIELDS, package_kind="KHAC")
