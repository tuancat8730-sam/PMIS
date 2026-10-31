import pytest

from app.services.beneficiary_units import display_dual_name

pytestmark = pytest.mark.unit


def test_dual_name_appends_former_name_with_cu_suffix() -> None:
    # Arrange
    official_name = "THPT Phan Bội Châu"
    former_name = "THPT Nguyễn Bỉnh Khiêm"

    # Act
    result = display_dual_name(official_name, former_name)

    # Assert
    assert result == "THPT Phan Bội Châu (THPT Nguyễn Bỉnh Khiêm cũ)"


def test_dual_name_returns_official_name_when_no_former_name() -> None:
    # Arrange
    official_name = "TH Nguyễn Văn Trỗi"

    # Act
    result = display_dual_name(official_name, None)

    # Assert
    assert result == "TH Nguyễn Văn Trỗi"


def test_dual_name_treats_blank_former_name_as_missing() -> None:
    # Arrange
    official_name = "THCS Minh Đức"

    # Act
    result = display_dual_name(official_name, "   ")

    # Assert
    assert result == "THCS Minh Đức"
