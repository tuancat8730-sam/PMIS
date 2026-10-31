import pytest
from pydantic import ValidationError

from app.models.contract_personnel import ContractPersonnel
from app.schemas.personnel import PersonnelCreate

pytestmark = pytest.mark.unit

BASE_FIELDS = {"full_name": "Nguyễn Quang Hân", "position_role": "Chủ nhiệm dự án"}


def test_cccd_with_spaces_is_normalized_to_twelve_digits() -> None:
    # Act
    personnel = PersonnelCreate(national_id_cccd="001 085 012 345", **BASE_FIELDS)

    # Assert
    assert personnel.national_id_cccd == "001085012345"


@pytest.mark.parametrize("cccd", ["12345", "00108501234A", "0010850123456"])
def test_cccd_that_is_not_twelve_digits_fails_validation(cccd: str) -> None:
    # Act / Assert
    with pytest.raises(ValidationError):
        PersonnelCreate(national_id_cccd=cccd, **BASE_FIELDS)


def test_personnel_without_cccd_is_accepted() -> None:
    # Act
    personnel = PersonnelCreate(**BASE_FIELDS)

    # Assert
    assert personnel.national_id_cccd is None


def test_masked_cccd_shows_only_last_four_digits() -> None:
    # Arrange
    personnel = ContractPersonnel(national_id_last4="2345")

    # Act / Assert
    assert personnel.national_id_masked == "********2345"


def test_masked_cccd_is_none_when_no_cccd_stored() -> None:
    # Arrange
    personnel = ContractPersonnel(national_id_last4=None)

    # Act / Assert
    assert personnel.national_id_masked is None
