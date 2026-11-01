import pytest

from app.core.contract_discrepancy_rules import closing_requires_resolution
from app.models.risk_issue import RecordType, RiskStatus

pytestmark = pytest.mark.unit


def test_closing_discrepancy_without_resolution_ref_is_blocked() -> None:
    # Arrange
    record_type = RecordType.CONTRACT_DISCREPANCY

    # Act
    blocked = closing_requires_resolution(record_type, RiskStatus.CLOSED, None)

    # Assert
    assert blocked is True


def test_closing_discrepancy_with_blank_resolution_ref_is_blocked() -> None:
    # Arrange
    record_type = RecordType.CONTRACT_DISCREPANCY

    # Act
    blocked = closing_requires_resolution(record_type, RiskStatus.RESOLVED, "   ")

    # Assert
    assert blocked is True


def test_closing_discrepancy_with_resolution_ref_is_allowed() -> None:
    # Arrange
    record_type = RecordType.CONTRACT_DISCREPANCY

    # Act
    blocked = closing_requires_resolution(record_type, RiskStatus.CLOSED, "Văn bản chốt số 12/CĐT")

    # Assert
    assert blocked is False


def test_open_discrepancy_does_not_need_resolution_ref() -> None:
    # Arrange
    record_type = RecordType.CONTRACT_DISCREPANCY

    # Act
    blocked = closing_requires_resolution(record_type, RiskStatus.IN_PROGRESS, None)

    # Assert
    assert blocked is False


def test_other_record_types_are_not_affected() -> None:
    # Arrange
    record_type = RecordType.RISK

    # Act
    blocked = closing_requires_resolution(record_type, RiskStatus.CLOSED, None)

    # Assert
    assert blocked is False
