from datetime import date

import pytest

from app.core.report_periods import ReportPeriod, week_period_containing

pytestmark = pytest.mark.unit


def test_week_period_starts_on_monday_and_ends_on_sunday() -> None:
    # Arrange
    day = date(2026, 10, 28)  # Thứ Tư

    # Act
    period = week_period_containing(day)

    # Assert
    assert period == ReportPeriod(start=date(2026, 10, 26), end=date(2026, 11, 1))


def test_monday_belongs_to_its_own_week() -> None:
    # Act
    period = week_period_containing(date(2026, 10, 26))

    # Assert
    assert period.start == date(2026, 10, 26)


def test_sunday_belongs_to_the_week_that_started_the_monday_before() -> None:
    # Act
    period = week_period_containing(date(2026, 11, 1))

    # Assert
    assert period.start == date(2026, 10, 26)
    assert period.end == date(2026, 11, 1)


def test_spec_week_three_matches_the_documented_range() -> None:
    # Act
    period = week_period_containing(date(2026, 10, 30))

    # Assert
    assert (period.start, period.end) == (date(2026, 10, 26), date(2026, 11, 1))


def test_period_end_is_always_six_days_after_start() -> None:
    # Arrange
    day = date(2026, 12, 31)

    # Act
    period = week_period_containing(day)

    # Assert
    assert (period.end - period.start).days == 6
