import pytest

from app.core.serial_shortage_rules import (
    CO_CQ_COMPLETE,
    CO_CQ_MISSING,
    CO_CQ_PARTIAL,
    DuplicateSerialError,
    co_cq_status,
    find_duplicate_serials,
    serial_shortage,
)

pytestmark = pytest.mark.unit


def test_shortage_is_required_minus_submitted_for_batch_one() -> None:
    # Arrange
    required = 1420
    submitted = 320

    # Act
    shortage = serial_shortage(required=required, submitted=submitted)

    # Assert
    assert shortage == 1100


def test_shortage_is_zero_when_submitted_meets_requirement() -> None:
    # Arrange / Act / Assert
    assert serial_shortage(required=10, submitted=10) == 0


def test_shortage_never_goes_negative_when_over_submitted() -> None:
    # Arrange / Act / Assert
    assert serial_shortage(required=10, submitted=12) == 0


def test_no_duplicates_returns_empty_tuple() -> None:
    # Arrange
    serials = ["SN001", "SN002", "SN003"]

    # Act
    duplicates = find_duplicate_serials(serials)

    # Assert
    assert duplicates == ()


def test_duplicates_are_reported_once_each_in_first_seen_order() -> None:
    # Arrange
    serials = ["SN001", "SN002", "SN001", "SN003", "SN002", "SN002"]

    # Act
    duplicates = find_duplicate_serials(serials)

    # Assert
    assert duplicates == ("SN001", "SN002")


def test_serials_are_compared_after_trimming_whitespace() -> None:
    # Arrange
    serials = ["SN001", "  SN001 "]

    # Act
    duplicates = find_duplicate_serials(serials)

    # Assert
    assert duplicates == ("SN001",)


def test_duplicate_serial_error_lists_the_offending_serials() -> None:
    # Arrange
    error = DuplicateSerialError(("SN001",))

    # Act / Assert
    assert "SN001" in str(error)


def test_co_cq_is_missing_when_no_document_attached() -> None:
    # Arrange / Act / Assert
    assert co_cq_status(required=1420, attached=0) == CO_CQ_MISSING


def test_co_cq_is_partial_when_some_documents_attached() -> None:
    # Arrange / Act / Assert
    assert co_cq_status(required=1420, attached=320) == CO_CQ_PARTIAL


def test_co_cq_is_complete_when_attached_meets_requirement() -> None:
    # Arrange / Act / Assert
    assert co_cq_status(required=1420, attached=1420) == CO_CQ_COMPLETE
