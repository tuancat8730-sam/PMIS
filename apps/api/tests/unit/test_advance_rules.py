from datetime import date
from decimal import Decimal

import pytest

from app.core.advance_rules import (
    advance_ceiling_amount,
    advance_within_ceiling,
    is_advance_on_time,
    working_days_between,
)

pytestmark = pytest.mark.unit

CONTRACT_VALUE = Decimal("100")
CEILING_PERCENT = Decimal("30")
MONDAY = date(2026, 11, 2)
TWENTY_WORKING_DAYS_LATER = date(2026, 11, 30)
TWENTY_ONE_WORKING_DAYS_LATER = date(2026, 12, 1)


def test_advance_ceiling_is_thirty_percent_of_contract_value() -> None:
    # Act
    ceiling = advance_ceiling_amount(CONTRACT_VALUE, CEILING_PERCENT)

    # Assert
    assert ceiling == Decimal("30.00")


def test_advance_equal_to_remaining_ceiling_is_accepted() -> None:
    # Act / Assert
    assert (
        advance_within_ceiling(
            contract_value=CONTRACT_VALUE,
            ceiling_percent=CEILING_PERCENT,
            already_granted=Decimal("0"),
            requested=Decimal("30"),
        )
        is True
    )


def test_advance_above_ceiling_is_rejected() -> None:
    # Act / Assert
    assert (
        advance_within_ceiling(
            contract_value=CONTRACT_VALUE,
            ceiling_percent=CEILING_PERCENT,
            already_granted=Decimal("0"),
            requested=Decimal("30.01"),
        )
        is False
    )


def test_advance_counts_previously_granted_amount_against_ceiling() -> None:
    # Act / Assert
    assert (
        advance_within_ceiling(
            contract_value=CONTRACT_VALUE,
            ceiling_percent=CEILING_PERCENT,
            already_granted=Decimal("20"),
            requested=Decimal("10.01"),
        )
        is False
    )


def test_working_days_between_skips_weekends() -> None:
    # Arrange
    friday = date(2026, 11, 6)

    # Act
    count = working_days_between(friday, date(2026, 11, 9), frozenset())

    # Assert
    assert count == 1


def test_working_days_between_same_day_is_zero() -> None:
    # Act / Assert
    assert working_days_between(MONDAY, MONDAY, frozenset()) == 0


def test_advance_decided_on_twentieth_working_day_is_on_time() -> None:
    # Act / Assert
    assert is_advance_on_time(MONDAY, TWENTY_WORKING_DAYS_LATER, 20, frozenset()) is True


def test_advance_decided_on_twenty_first_working_day_is_late() -> None:
    # Act / Assert
    assert is_advance_on_time(MONDAY, TWENTY_ONE_WORKING_DAYS_LATER, 20, frozenset()) is False


def test_non_working_day_extends_the_advance_deadline() -> None:
    # Arrange: 3/11 là ngày nghỉ, nên hạn 20 ngày làm việc lùi sang 1/12
    holidays = frozenset({date(2026, 11, 3)})

    # Act / Assert
    assert is_advance_on_time(MONDAY, TWENTY_ONE_WORKING_DAYS_LATER, 20, holidays) is True
    assert is_advance_on_time(MONDAY, date(2026, 12, 2), 20, holidays) is False
