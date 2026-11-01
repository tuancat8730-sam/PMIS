import pytest

from app.core.sample_criteria import (
    CONCLUSION_PASSED,
    CONCLUSION_REWORK,
    SampleInspectionError,
    approval_status_for,
    ensure_codes_match_catalog,
)

pytestmark = pytest.mark.unit


def test_passed_conclusion_maps_to_approved_sample_status() -> None:
    # Arrange / Act
    status = approval_status_for(CONCLUSION_PASSED)

    # Assert
    assert status == "APPROVED"


def test_rework_conclusion_maps_to_rework_required_sample_status() -> None:
    # Arrange / Act
    status = approval_status_for(CONCLUSION_REWORK)

    # Assert
    assert status == "REWORK_REQUIRED"


def test_unknown_conclusion_is_rejected() -> None:
    # Arrange / Act / Assert
    with pytest.raises(ValueError, match="Kết luận không xác định"):
        approval_status_for("CHƯA RÕ")


def test_submitted_codes_match_catalog_regardless_of_order() -> None:
    # Arrange
    submitted = ["TC02", "TC01"]
    catalog = ["TC01", "TC02"]

    # Act / Assert
    ensure_codes_match_catalog(submitted, catalog)


def test_submitted_codes_missing_a_catalog_code_are_rejected() -> None:
    # Arrange
    submitted = ["TC01"]
    catalog = ["TC01", "TC02"]

    # Act / Assert
    with pytest.raises(SampleInspectionError, match="Mã tiêu chí không khớp danh mục"):
        ensure_codes_match_catalog(submitted, catalog)


def test_submitted_code_outside_catalog_is_rejected() -> None:
    # Arrange
    submitted = ["TC01", "TC99"]
    catalog = ["TC01", "TC02"]

    # Act / Assert
    with pytest.raises(SampleInspectionError, match="Mã tiêu chí không khớp danh mục"):
        ensure_codes_match_catalog(submitted, catalog)
