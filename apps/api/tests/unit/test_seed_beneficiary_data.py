from pathlib import Path

import pytest

from app.db.seed_real_projects import HCM_UNITS_FILE, load_units
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


@pytest.mark.skip(reason="B1: chờ danh sách 62 đơn vị Lâm Đồng (file xlsx từ người dùng)")
def test_lam_dong_seed_has_62_units_in_four_clusters_15_19_14_14() -> None:
    pass
