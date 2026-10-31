import pytest

from app.core.legal_maturity_rules import can_transition, is_locked, requires_reason
from app.models.legal_document import DocMaturityStatus

pytestmark = pytest.mark.unit

MISSING = DocMaturityStatus.MISSING
DRAFT_DOCX = DocMaturityStatus.DRAFT_DOCX
SUBMITTED_REVIEW = DocMaturityStatus.SUBMITTED_REVIEW
WAITING_SIGNATURE = DocMaturityStatus.WAITING_SIGNATURE
SIGNED_SCAN_PDF = DocMaturityStatus.SIGNED_SCAN_PDF
DISCREPANCY_FOUND = DocMaturityStatus.DISCREPANCY_FOUND
VERIFIED_CLOSED = DocMaturityStatus.VERIFIED_CLOSED


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (MISSING, DRAFT_DOCX),
        (DRAFT_DOCX, SUBMITTED_REVIEW),
        (SUBMITTED_REVIEW, WAITING_SIGNATURE),
        (WAITING_SIGNATURE, SIGNED_SCAN_PDF),
        (SIGNED_SCAN_PDF, VERIFIED_CLOSED),
    ],
)
def test_next_step_in_the_chain_is_allowed_without_reason(
    current: DocMaturityStatus,
    target: DocMaturityStatus,
) -> None:
    # Arrange
    # Act
    allowed = can_transition(current, target)
    needs_reason = requires_reason(current, target)

    # Assert
    assert allowed is True
    assert needs_reason is False


def test_skipping_a_step_is_rejected() -> None:
    # Arrange
    # Act
    allowed = can_transition(MISSING, SUBMITTED_REVIEW)

    # Assert
    assert allowed is False


def test_same_status_is_rejected() -> None:
    # Arrange
    # Act
    allowed = can_transition(DRAFT_DOCX, DRAFT_DOCX)

    # Assert
    assert allowed is False


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (SUBMITTED_REVIEW, DRAFT_DOCX),
        (WAITING_SIGNATURE, DRAFT_DOCX),
        (SIGNED_SCAN_PDF, SUBMITTED_REVIEW),
    ],
)
def test_moving_backward_is_allowed_but_requires_reason(
    current: DocMaturityStatus,
    target: DocMaturityStatus,
) -> None:
    # Arrange
    # Act
    allowed = can_transition(current, target)
    needs_reason = requires_reason(current, target)

    # Assert
    assert allowed is True
    assert needs_reason is True


@pytest.mark.parametrize(
    "current",
    [SUBMITTED_REVIEW, WAITING_SIGNATURE, SIGNED_SCAN_PDF],
)
def test_discrepancy_can_be_raised_from_review_stages_and_requires_reason(
    current: DocMaturityStatus,
) -> None:
    # Arrange
    # Act
    allowed = can_transition(current, DISCREPANCY_FOUND)
    needs_reason = requires_reason(current, DISCREPANCY_FOUND)

    # Assert
    assert allowed is True
    assert needs_reason is True


def test_discrepancy_can_only_go_back_to_draft() -> None:
    # Arrange
    # Act
    back_to_draft = can_transition(DISCREPANCY_FOUND, DRAFT_DOCX)
    to_signed = can_transition(DISCREPANCY_FOUND, SIGNED_SCAN_PDF)

    # Assert
    assert back_to_draft is True
    assert to_signed is False


def test_verified_closed_is_locked_and_only_reopens_to_signed_scan() -> None:
    # Arrange
    # Act
    locked = is_locked(VERIFIED_CLOSED)
    reopen = can_transition(VERIFIED_CLOSED, SIGNED_SCAN_PDF)
    reopen_needs_reason = requires_reason(VERIFIED_CLOSED, SIGNED_SCAN_PDF)
    to_draft = can_transition(VERIFIED_CLOSED, DRAFT_DOCX)

    # Assert
    assert locked is True
    assert reopen is True
    assert reopen_needs_reason is True
    assert to_draft is False


@pytest.mark.parametrize("status", [MISSING, DRAFT_DOCX, SIGNED_SCAN_PDF, DISCREPANCY_FOUND])
def test_only_verified_closed_is_locked(status: DocMaturityStatus) -> None:
    # Arrange
    # Act
    locked = is_locked(status)

    # Assert
    assert locked is False
