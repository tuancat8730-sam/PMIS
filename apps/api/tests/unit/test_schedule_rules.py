from datetime import date
from decimal import Decimal

import pytest

from app.core.schedule_rules import (
    derive_milestone_status,
    effective_due_date,
    hard_deadline_respected,
    missing_confirmation_parties,
    penalty_amount,
    slippage_days,
)
from app.models.milestone import MilestoneStatus, StoredMilestoneStatus

pytestmark = pytest.mark.unit

TODAY = date(2026, 11, 10)


def test_effective_due_date_uses_adjusted_end_when_present() -> None:
    # Arrange
    baseline_end = date(2026, 10, 7)
    adjusted_end = date(2026, 11, 5)

    # Act
    due = effective_due_date(baseline_end, adjusted_end)

    # Assert
    assert due == adjusted_end


def test_effective_due_date_falls_back_to_baseline_end() -> None:
    # Arrange
    baseline_end = date(2026, 11, 30)

    # Act
    due = effective_due_date(baseline_end, None)

    # Assert
    assert due == baseline_end


def test_slippage_is_negative_when_finished_before_due() -> None:
    # Arrange
    due = date(2026, 11, 5)
    actual_end = date(2026, 11, 1)

    # Act
    days = slippage_days(due, actual_end, TODAY)

    # Assert
    assert days == -4


def test_slippage_uses_today_when_milestone_still_open() -> None:
    # Arrange
    due = date(2026, 11, 5)

    # Act
    days = slippage_days(due, None, TODAY)

    # Assert
    assert days == 5


def test_penalty_is_rate_times_days_times_contract_value() -> None:
    # Arrange
    contract_value = Decimal("1000000000.00")
    rate_per_day = Decimal("0.001")
    cap_percent = Decimal("8.00")

    # Act
    amount = penalty_amount(contract_value, 10, rate_per_day, cap_percent)

    # Assert
    assert amount == Decimal("10000000.00")


def test_penalty_is_capped_at_cap_percent_of_contract_value() -> None:
    # Arrange
    contract_value = Decimal("1000000000.00")
    rate_per_day = Decimal("0.001")
    cap_percent = Decimal("8.00")

    # Act
    amount = penalty_amount(contract_value, 500, rate_per_day, cap_percent)

    # Assert
    assert amount == Decimal("80000000.00")


def test_penalty_is_zero_when_not_late() -> None:
    # Arrange
    contract_value = Decimal("1000000000.00")

    # Act
    amount = penalty_amount(contract_value, -3, Decimal("0.001"), Decimal("8.00"))

    # Assert
    assert amount == Decimal("0.00")


def test_hard_deadline_rejects_adjusted_end_after_baseline() -> None:
    # Arrange
    baseline_end = date(2026, 11, 30)
    adjusted_end = date(2026, 12, 2)

    # Act
    respected = hard_deadline_respected(True, baseline_end, adjusted_end)

    # Assert
    assert respected is False


def test_hard_deadline_accepts_earlier_adjusted_end() -> None:
    # Arrange
    baseline_end = date(2026, 11, 30)
    adjusted_end = date(2026, 11, 25)

    # Act
    respected = hard_deadline_respected(True, baseline_end, adjusted_end)

    # Assert
    assert respected is True


def test_soft_milestone_may_move_past_baseline() -> None:
    # Arrange
    baseline_end = date(2026, 10, 7)
    adjusted_end = date(2026, 11, 5)

    # Act
    respected = hard_deadline_respected(False, baseline_end, adjusted_end)

    # Assert
    assert respected is True


def test_status_becomes_overdue_when_past_due_and_open() -> None:
    # Arrange
    baseline_end = date(2026, 10, 7)

    # Act
    status = derive_milestone_status(
        StoredMilestoneStatus.IN_PROGRESS, baseline_end, None, None, TODAY
    )

    # Assert
    assert status == MilestoneStatus.OVERDUE


def test_status_becomes_at_risk_when_adjusted_past_baseline() -> None:
    # Arrange
    baseline_end = date(2026, 10, 7)
    adjusted_end = date(2026, 11, 20)

    # Act
    status = derive_milestone_status(
        StoredMilestoneStatus.IN_PROGRESS, baseline_end, adjusted_end, None, TODAY
    )

    # Assert
    assert status == MilestoneStatus.AT_RISK


def test_completed_status_is_never_overridden() -> None:
    # Arrange
    baseline_end = date(2026, 10, 7)

    # Act
    status = derive_milestone_status(
        StoredMilestoneStatus.COMPLETED, baseline_end, None, date(2026, 10, 6), TODAY
    )

    # Assert
    assert status == MilestoneStatus.COMPLETED


def test_missing_parties_lists_each_unconfirmed_party() -> None:
    # Arrange
    required = frozenset({"CDT", "TVGS", "NHA_THAU"})
    confirmed = {"CDT"}

    # Act
    missing = missing_confirmation_parties(confirmed, required)

    # Assert
    assert missing == {"TVGS", "NHA_THAU"}


def test_no_missing_parties_when_all_confirmed() -> None:
    # Arrange
    required = frozenset({"CDT", "TVGS", "NHA_THAU"})

    # Act
    missing = missing_confirmation_parties({"CDT", "TVGS", "NHA_THAU"}, required)

    # Assert
    assert missing == set()
