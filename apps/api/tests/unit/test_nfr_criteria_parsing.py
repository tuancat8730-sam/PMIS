from decimal import Decimal

import pytest

from app.core.nfr_rules import Comparison, NfrCriterion, criteria_from_json

pytestmark = pytest.mark.unit


def test_parses_comparison_and_threshold_from_json_mapping() -> None:
    # Arrange
    raw = {"ccu": {"comparison": "AT_LEAST", "threshold": "3600"}}

    # Act
    criteria = criteria_from_json(raw)

    # Assert
    assert criteria == (NfrCriterion("ccu", Comparison.AT_LEAST, Decimal("3600")),)


def test_accepts_numeric_threshold_given_as_float_string_with_decimal_precision() -> None:
    # Arrange
    raw = {"uptime_percent": {"comparison": "AT_LEAST", "threshold": 99.9}}

    # Act
    criteria = criteria_from_json(raw)

    # Assert
    assert criteria[0].threshold == Decimal("99.9")


def test_unknown_comparison_is_rejected_with_value_error() -> None:
    # Arrange
    raw = {"ccu": {"comparison": "EQUALS", "threshold": "3600"}}

    # Act / Assert
    with pytest.raises(ValueError):
        criteria_from_json(raw)


def test_non_numeric_threshold_is_rejected_with_value_error() -> None:
    # Arrange
    raw = {"ccu": {"comparison": "AT_LEAST", "threshold": "nhiều"}}

    # Act / Assert
    with pytest.raises(ValueError):
        criteria_from_json(raw)


def test_missing_threshold_is_rejected_with_value_error() -> None:
    # Arrange
    raw = {"ccu": {"comparison": "AT_LEAST"}}

    # Act / Assert
    with pytest.raises(ValueError):
        criteria_from_json(raw)


def test_empty_mapping_gives_no_criteria() -> None:
    # Arrange
    raw: dict[str, dict[str, str]] = {}

    # Act
    criteria = criteria_from_json(raw)

    # Assert
    assert criteria == ()
