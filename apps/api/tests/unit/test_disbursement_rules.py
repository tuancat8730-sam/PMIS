from datetime import date
from decimal import Decimal

import pytest

from app.core.disbursement_rules import (
    days_until,
    disbursement_rate,
    exceeds_plan,
    lock_warning_active,
)

pytestmark = pytest.mark.unit

LOCK_ON = date(2026, 12, 9)
WARN_DAYS = 15


def test_disbursement_rate_is_paid_over_planned_percent() -> None:
    # Act / Assert
    assert disbursement_rate(Decimal("50"), Decimal("200")) == Decimal("25.00")


def test_disbursement_rate_rounds_to_two_decimals() -> None:
    # Act / Assert
    assert disbursement_rate(Decimal("100"), Decimal("300")) == Decimal("33.33")


def test_disbursement_rate_is_zero_when_nothing_is_planned() -> None:
    # Act / Assert
    assert disbursement_rate(Decimal("10"), Decimal("0")) == Decimal("0.00")


def test_days_until_counts_calendar_days_to_target() -> None:
    # Act / Assert
    assert days_until(LOCK_ON, date(2026, 11, 24)) == 15


def test_lock_warning_starts_exactly_warn_days_before_lock() -> None:
    # Act / Assert
    assert lock_warning_active(LOCK_ON, date(2026, 11, 24), WARN_DAYS) is True


def test_lock_warning_not_yet_active_one_day_earlier() -> None:
    # Act / Assert
    assert lock_warning_active(LOCK_ON, date(2026, 11, 23), WARN_DAYS) is False


def test_lock_warning_is_active_on_lock_day() -> None:
    # Act / Assert
    assert lock_warning_active(LOCK_ON, LOCK_ON, WARN_DAYS) is True


def test_lock_warning_is_not_active_after_lock_day() -> None:
    # Act / Assert
    assert lock_warning_active(LOCK_ON, date(2026, 12, 10), WARN_DAYS) is False


def test_paid_above_planned_amount_is_flagged_as_exceeding_plan() -> None:
    # Act / Assert
    assert exceeds_plan(Decimal("200.01"), Decimal("200")) is True


def test_paid_equal_to_planned_amount_is_not_flagged() -> None:
    # Act / Assert
    assert exceeds_plan(Decimal("200"), Decimal("200")) is False
