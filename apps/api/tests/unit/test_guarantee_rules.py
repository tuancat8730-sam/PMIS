from datetime import date
from decimal import Decimal

import pytest

from app.core.guarantee_rules import (
    guarantee_amount,
    guarantee_is_expired,
    poa_expired_before_issue,
)

pytestmark = pytest.mark.unit


def test_guarantee_amount_is_three_percent_of_contract_value() -> None:
    # Arrange
    contract_value = Decimal("1000000000.00")

    # Act
    amount = guarantee_amount(contract_value, Decimal("3"))

    # Assert
    assert amount == Decimal("30000000.00")


def test_guarantee_amount_rounds_half_up_to_cents() -> None:
    # Arrange
    contract_value = Decimal("100.50")

    # Act
    amount = guarantee_amount(contract_value, Decimal("3"))

    # Assert
    assert amount == Decimal("3.02")


def test_guarantee_is_still_valid_on_its_expiry_date() -> None:
    # Arrange
    expires_on = date(2026, 12, 31)

    # Act / Assert
    assert guarantee_is_expired(expires_on, date(2026, 12, 31)) is False


def test_guarantee_is_expired_the_day_after_expiry() -> None:
    # Arrange
    expires_on = date(2026, 12, 31)

    # Act / Assert
    assert guarantee_is_expired(expires_on, date(2027, 1, 1)) is True


def test_poa_expiring_before_issue_date_is_flagged() -> None:
    # Arrange
    issued_on = date(2026, 11, 1)
    poa_expires_on = date(2026, 10, 31)

    # Act / Assert
    assert poa_expired_before_issue(issued_on, poa_expires_on) is True


def test_poa_expiring_on_issue_date_is_not_flagged() -> None:
    # Arrange
    issued_on = date(2026, 11, 1)

    # Act / Assert
    assert poa_expired_before_issue(issued_on, date(2026, 11, 1)) is False
