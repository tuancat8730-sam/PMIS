from datetime import date
from decimal import Decimal

import pytest

from app.core.command_center_rules import (
    MilestoneTiming,
    build_health_inputs,
    is_red_milestone,
    sum_contract_values_by_kind,
)
from app.core.project_health import ProjectHealthInputs

pytestmark = pytest.mark.unit

TODAY = date(2026, 11, 1)


def _timing(
    *,
    baseline_end: date,
    adjusted_end: date | None = None,
    actual_end: date | None = None,
    is_hard_deadline: bool = False,
) -> MilestoneTiming:
    return MilestoneTiming(
        baseline_end=baseline_end,
        adjusted_end=adjusted_end,
        actual_end=actual_end,
        is_hard_deadline=is_hard_deadline,
    )


def test_health_inputs_take_the_largest_slippage_among_milestones() -> None:
    # Arrange
    milestones = [
        _timing(baseline_end=date(2026, 10, 20)),  # trễ 12 ngày, chưa xong
        _timing(baseline_end=date(2026, 10, 30)),  # trễ 2 ngày
    ]

    # Act
    inputs = build_health_inputs(milestones, red_alert_count=0, is_completed=False, today=TODAY)

    # Assert
    assert inputs == ProjectHealthInputs(
        is_completed=False,
        hard_deadline_late=False,
        max_slippage_days=12,
        red_alert_count=0,
    )


def test_completed_milestone_keeps_its_historical_slippage() -> None:
    # Arrange: xong trễ 5 ngày, không còn mở
    milestones = [
        _timing(baseline_end=date(2026, 10, 1), actual_end=date(2026, 10, 6)),
    ]

    # Act
    inputs = build_health_inputs(milestones, red_alert_count=0, is_completed=False, today=TODAY)

    # Assert
    assert inputs.max_slippage_days == 5


def test_early_finish_does_not_count_as_slippage() -> None:
    # Arrange
    milestones = [
        _timing(baseline_end=date(2026, 10, 30), actual_end=date(2026, 10, 20)),
    ]

    # Act
    inputs = build_health_inputs(milestones, red_alert_count=0, is_completed=False, today=TODAY)

    # Assert
    assert inputs.max_slippage_days == 0


def test_late_hard_deadline_is_flagged() -> None:
    # Arrange
    milestones = [
        _timing(baseline_end=date(2026, 10, 30), is_hard_deadline=True),
    ]

    # Act
    inputs = build_health_inputs(milestones, red_alert_count=0, is_completed=False, today=TODAY)

    # Assert
    assert inputs.hard_deadline_late is True


def test_late_soft_deadline_is_not_a_hard_deadline_breach() -> None:
    # Arrange
    milestones = [_timing(baseline_end=date(2026, 10, 30))]

    # Act
    inputs = build_health_inputs(milestones, red_alert_count=0, is_completed=False, today=TODAY)

    # Assert
    assert inputs.hard_deadline_late is False


def test_project_without_milestones_has_no_slippage() -> None:
    # Act
    inputs = build_health_inputs([], red_alert_count=2, is_completed=False, today=TODAY)

    # Assert
    assert inputs.max_slippage_days == 0
    assert inputs.red_alert_count == 2


def test_red_milestone_is_open_and_due_within_window_or_overdue() -> None:
    # Arrange
    due_in_window = _timing(baseline_end=date(2026, 11, 3))  # còn trong 48 giờ, mở
    overdue = _timing(baseline_end=date(2026, 10, 25))  # quá hạn, mở
    finished = _timing(baseline_end=date(2026, 11, 3), actual_end=date(2026, 11, 1))
    far_away = _timing(baseline_end=date(2026, 11, 20))  # xa, không đỏ

    # Act / Assert
    assert is_red_milestone(due_in_window, TODAY) is True
    assert is_red_milestone(overdue, TODAY) is True
    assert is_red_milestone(finished, TODAY) is False
    assert is_red_milestone(far_away, TODAY) is False


def test_contract_values_are_summed_per_package_kind() -> None:
    # Arrange
    contracts = [
        ("MAIN", Decimal("100.00")),
        ("MAIN", Decimal("11.07")),
        ("CONSULTING", Decimal("1.12")),
    ]

    # Act
    totals = sum_contract_values_by_kind(contracts)

    # Assert
    assert totals == {"MAIN": Decimal("111.07"), "CONSULTING": Decimal("1.12")}


def test_package_kind_without_contracts_reports_zero() -> None:
    # Act
    totals = sum_contract_values_by_kind([])

    # Assert
    assert totals == {"MAIN": Decimal("0"), "CONSULTING": Decimal("0")}
