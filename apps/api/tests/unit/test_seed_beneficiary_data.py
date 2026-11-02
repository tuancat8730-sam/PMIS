from collections import Counter
from pathlib import Path

import pytest

from app.db.seed_real_projects import HCM_UNITS_FILE, LAM_DONG_UNITS_FILE, load_units
from app.schemas.beneficiary_units import BeneficiaryUnitCreate

pytestmark = pytest.mark.unit

HCM_SURVEY_UNIT_NAMES = {
    "THPT Chuyên Lê Hồng Phong",
    "TH Nguyễn Bỉnh Khiêm",
    "THCS Minh Đức",
    "TH Nguyễn Văn Trỗi",
    "THCS Trần Văn Ơn",
    "THPT Hùng Vương",
    "UBND P. Sài Gòn",
    "UBND P. Cầu Ông Lãnh",
}


def test_hcm_seed_file_contains_the_eight_survey_units_from_spec() -> None:
    # Arrange
    path: Path = HCM_UNITS_FILE

    # Act
    rows = load_units(path)

    # Assert
    assert len(rows) == 8
    assert {row["official_name"] for row in rows} == HCM_SURVEY_UNIT_NAMES


def test_hcm_seed_rows_pass_the_same_validation_as_the_api() -> None:
    # Arrange
    rows = load_units(HCM_UNITS_FILE)

    # Act
    validated = [BeneficiaryUnitCreate(**row) for row in rows]

    # Assert
    assert len(validated) == 8


def test_hcm_seed_unit_codes_are_unique() -> None:
    # Arrange
    rows = load_units(HCM_UNITS_FILE)

    # Act
    codes = [row["unit_code"] for row in rows]

    # Assert
    assert len(set(codes)) == len(codes)


def test_lam_dong_seed_has_62_units_in_four_clusters_15_19_14_14() -> None:
    # Arrange
    rows = load_units(LAM_DONG_UNITS_FILE)

    # Act
    cluster_sizes = Counter(row["cluster_code"] for row in rows)

    # Assert
    assert len(rows) == 62
    assert cluster_sizes == {"LD-C1": 15, "LD-C2": 19, "LD-C3": 14, "LD-C4": 14}


def test_lam_dong_seed_rows_pass_the_same_validation_as_the_api() -> None:
    # Arrange
    rows = load_units(LAM_DONG_UNITS_FILE)

    # Act
    validated = [BeneficiaryUnitCreate(**row) for row in rows]

    # Assert
    assert len(validated) == 62


def test_lam_dong_seed_unit_codes_are_unique() -> None:
    # Arrange
    rows = load_units(LAM_DONG_UNITS_FILE)

    # Act
    codes = [row["unit_code"] for row in rows]

    # Assert
    assert len(set(codes)) == len(codes)


def test_lam_dong_seed_marks_the_nine_merged_away_schools() -> None:
    # Arrange
    rows = load_units(LAM_DONG_UNITS_FILE)

    # Act
    merged = [row for row in rows if "đã sáp nhập" in row["official_name"]]

    # Assert
    assert len(merged) == 9
    assert all(row["principal_name"] is None for row in merged)
