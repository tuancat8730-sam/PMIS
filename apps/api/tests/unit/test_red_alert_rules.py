from datetime import date

import pytest

from app.core.red_alert_rules import RED_ALERT_WINDOW_DAYS, is_red_alert

pytestmark = pytest.mark.unit

TODAY = date(2026, 11, 1)


def test_window_is_two_days_for_forty_eight_hours() -> None:
    # Assert
    assert RED_ALERT_WINDOW_DAYS == 2


def test_item_due_today_is_red() -> None:
    # Act
    red = is_red_alert(TODAY, TODAY)

    # Assert
    assert red is True


def test_item_due_within_window_is_red() -> None:
    # Arrange
    due = date(2026, 11, 3)  # đúng 48 giờ

    # Act
    red = is_red_alert(due, TODAY)

    # Assert
    assert red is True


def test_item_due_after_window_is_not_red() -> None:
    # Arrange
    due = date(2026, 11, 4)  # quá 48 giờ

    # Act
    red = is_red_alert(due, TODAY)

    # Assert
    assert red is False


def test_overdue_item_is_red() -> None:
    # Arrange
    due = date(2026, 10, 25)

    # Act
    red = is_red_alert(due, TODAY)

    # Assert
    assert red is True


def test_missing_due_date_is_never_red() -> None:
    # Act
    red = is_red_alert(None, TODAY)

    # Assert
    assert red is False
