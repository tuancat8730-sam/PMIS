from decimal import Decimal

import pytest

from app.core.nfr_rules import (
    Comparison,
    NfrCriterion,
    all_passed,
    evaluate_nfr,
    meets,
)

pytestmark = pytest.mark.unit


def test_ccu_at_least_3600_passes_on_exact_boundary() -> None:
    # Arrange
    criterion = NfrCriterion("ccu", Comparison.AT_LEAST, Decimal("3600"))

    # Act
    passed = meets(Decimal("3600"), criterion)

    # Assert
    assert passed is True


def test_ccu_at_least_3600_fails_one_below_boundary() -> None:
    # Arrange
    criterion = NfrCriterion("ccu", Comparison.AT_LEAST, Decimal("3600"))

    # Act
    passed = meets(Decimal("3599"), criterion)

    # Assert
    assert passed is False


def test_accounts_at_least_5170_fails_one_below_boundary() -> None:
    # Arrange
    criterion = NfrCriterion("accounts", Comparison.AT_LEAST, Decimal("5170"))

    # Act
    passed = meets(Decimal("5169"), criterion)

    # Assert
    assert passed is False


def test_average_response_below_2s_fails_exactly_at_2s() -> None:
    # Arrange
    criterion = NfrCriterion("avg_response_s", Comparison.BELOW, Decimal("2"))

    # Act
    passed = meets(Decimal("2"), criterion)

    # Assert
    assert passed is False


def test_average_response_below_2s_passes_just_under() -> None:
    # Arrange
    criterion = NfrCriterion("avg_response_s", Comparison.BELOW, Decimal("2"))

    # Act
    passed = meets(Decimal("1.99"), criterion)

    # Assert
    assert passed is True


def test_4g_page_load_below_3s_fails_exactly_at_3s() -> None:
    # Arrange
    criterion = NfrCriterion("page_load_4g_s", Comparison.BELOW, Decimal("3"))

    # Act
    passed = meets(Decimal("3"), criterion)

    # Assert
    assert passed is False


def test_complex_report_at_most_10s_passes_on_exact_boundary() -> None:
    # Arrange
    criterion = NfrCriterion("report_s", Comparison.AT_MOST, Decimal("10"))

    # Act
    passed = meets(Decimal("10"), criterion)

    # Assert
    assert passed is True


def test_complex_report_at_most_10s_fails_just_over() -> None:
    # Arrange
    criterion = NfrCriterion("report_s", Comparison.AT_MOST, Decimal("10"))

    # Act
    passed = meets(Decimal("10.01"), criterion)

    # Assert
    assert passed is False


def test_uptime_at_least_99_9_passes_on_exact_boundary() -> None:
    # Arrange
    criterion = NfrCriterion("uptime_percent", Comparison.AT_LEAST, Decimal("99.9"))

    # Act
    passed = meets(Decimal("99.9"), criterion)

    # Assert
    assert passed is True


def test_uptime_at_least_99_9_fails_just_under() -> None:
    # Arrange
    criterion = NfrCriterion("uptime_percent", Comparison.AT_LEAST, Decimal("99.9"))

    # Act
    passed = meets(Decimal("99.89"), criterion)

    # Assert
    assert passed is False


def test_rto_at_most_4h_passes_on_exact_boundary() -> None:
    # Arrange
    criterion = NfrCriterion("rto_hours", Comparison.AT_MOST, Decimal("4"))

    # Act
    passed = meets(Decimal("4"), criterion)

    # Assert
    assert passed is True


def test_rto_at_most_4h_fails_just_over() -> None:
    # Arrange
    criterion = NfrCriterion("rto_hours", Comparison.AT_MOST, Decimal("4"))

    # Act
    passed = meets(Decimal("4.5"), criterion)

    # Assert
    assert passed is False


def test_backup_retention_at_least_30_days_fails_one_below() -> None:
    # Arrange
    criterion = NfrCriterion("backup_retention_days", Comparison.AT_LEAST, Decimal("30"))

    # Act
    passed = meets(Decimal("29"), criterion)

    # Assert
    assert passed is False


def test_audit_retention_at_least_12_months_passes_on_exact_boundary() -> None:
    # Arrange
    criterion = NfrCriterion("audit_retention_months", Comparison.AT_LEAST, Decimal("12"))

    # Act
    passed = meets(Decimal("12"), criterion)

    # Assert
    assert passed is True


def test_threshold_is_argument_not_hard_coded() -> None:
    # Arrange
    strict = NfrCriterion("ccu", Comparison.AT_LEAST, Decimal("4000"))
    loose = NfrCriterion("ccu", Comparison.AT_LEAST, Decimal("1000"))

    # Act
    strict_result = meets(Decimal("3600"), strict)
    loose_result = meets(Decimal("3600"), loose)

    # Assert
    assert strict_result is False
    assert loose_result is True


def test_missing_measurement_counts_as_not_passed() -> None:
    # Arrange
    criteria = (NfrCriterion("ccu", Comparison.AT_LEAST, Decimal("3600")),)

    # Act
    results = evaluate_nfr(criteria, {})

    # Assert
    assert results[0].passed is False
    assert results[0].measured is None


def test_evaluate_nfr_keeps_criteria_order_and_reports_each() -> None:
    # Arrange
    criteria = (
        NfrCriterion("ccu", Comparison.AT_LEAST, Decimal("3600")),
        NfrCriterion("rto_hours", Comparison.AT_MOST, Decimal("4")),
    )
    measurements = {"ccu": Decimal("3700"), "rto_hours": Decimal("5")}

    # Act
    results = evaluate_nfr(criteria, measurements)

    # Assert
    assert [(r.key, r.passed) for r in results] == [("ccu", True), ("rto_hours", False)]


def test_all_passed_is_false_when_any_criterion_fails() -> None:
    # Arrange
    criteria = (
        NfrCriterion("ccu", Comparison.AT_LEAST, Decimal("3600")),
        NfrCriterion("rto_hours", Comparison.AT_MOST, Decimal("4")),
    )
    results = evaluate_nfr(criteria, {"ccu": Decimal("3700"), "rto_hours": Decimal("5")})

    # Act
    passed = all_passed(results)

    # Assert
    assert passed is False


def test_all_passed_is_false_for_empty_criteria() -> None:
    # Arrange
    results = evaluate_nfr((), {})

    # Act
    passed = all_passed(results)

    # Assert
    assert passed is False
