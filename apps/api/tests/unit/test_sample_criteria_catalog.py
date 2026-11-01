import pytest

from app.core.sample_criteria_catalog import SAMPLE_CRITERIA

pytestmark = pytest.mark.unit

CATALOG_SIZE = 21


def test_catalog_contains_exactly_21_criteria() -> None:
    # Arrange / Act
    count = len(SAMPLE_CRITERIA)

    # Assert
    assert count == CATALOG_SIZE


def test_criterion_codes_are_unique() -> None:
    # Arrange
    codes = [criterion.code for criterion in SAMPLE_CRITERIA]

    # Act / Assert
    assert len(set(codes)) == len(codes)


def test_every_criterion_has_a_non_empty_vietnamese_label() -> None:
    # Arrange / Act / Assert
    for criterion in SAMPLE_CRITERIA:
        assert criterion.label.strip(), f"Thiếu nhãn cho {criterion.code}"
