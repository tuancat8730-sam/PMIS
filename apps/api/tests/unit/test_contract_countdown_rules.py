from datetime import date

import pytest

from app.core.contract_countdown import (
    CountdownStatus,
    countdown_status,
    days_until_expiration,
)

pytestmark = pytest.mark.unit

TODAY = date(2026, 11, 1)


def test_days_until_expiration_counts_calendar_days() -> None:
    # Arrange
    expiration = date(2026, 12, 1)

    # Act
    remaining = days_until_expiration(expiration, TODAY)

    # Assert
    assert remaining == 30


def test_days_until_expiration_is_negative_after_expiry() -> None:
    # Arrange
    expiration = date(2026, 10, 31)

    # Act
    remaining = days_until_expiration(expiration, TODAY)

    # Assert
    assert remaining == -1


def test_warning_starts_exactly_at_thirty_days_remaining() -> None:
    # Arrange
    expiration = date(2026, 12, 1)  # còn 30 ngày

    # Act
    status = countdown_status(expiration, TODAY)

    # Assert
    assert status == CountdownStatus.WARNING


def test_no_warning_at_thirty_one_days_remaining() -> None:
    # Arrange
    expiration = date(2026, 12, 2)  # còn 31 ngày

    # Act
    status = countdown_status(expiration, TODAY)

    # Assert
    assert status == CountdownStatus.OK


def test_expired_contract_is_reported_as_expired() -> None:
    # Arrange
    expiration = date(2026, 10, 1)

    # Act
    status = countdown_status(expiration, TODAY)

    # Assert
    assert status == CountdownStatus.EXPIRED


def test_missing_expiration_date_reports_no_date() -> None:
    # Arrange
    expiration = None

    # Act
    status = countdown_status(expiration, TODAY)

    # Assert
    assert status == CountdownStatus.NO_DATE


def test_custom_warning_window_is_respected() -> None:
    # Arrange
    expiration = date(2026, 11, 11)  # còn 10 ngày

    # Act
    status = countdown_status(expiration, TODAY, warning_days=7)

    # Assert
    assert status == CountdownStatus.OK
