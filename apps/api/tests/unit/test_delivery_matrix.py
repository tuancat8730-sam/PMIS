import pytest

from app.core.delivery_matrix import (
    BATCH_CODES,
    OVERALL_BATCH_CODE,
    STATUS_IN_TRANSIT,
    STATUS_INSTALLED,
    STATUS_ISSUE_REPORTED,
    STATUS_SCHEDULED,
    STATUS_SIGNED_HANDOVER,
    DeliveryMatrixError,
    DeliveryTransitionError,
    build_handover_slots,
    change_delivery_status,
)

pytestmark = pytest.mark.unit

UNIT_COUNT = 62


def _unit_ids(count: int = UNIT_COUNT) -> list[str]:
    return [f"unit-{index:02d}" for index in range(1, count + 1)]


def test_matrix_has_one_row_per_unit_per_batch_plus_overall_row() -> None:
    # Arrange
    unit_ids = _unit_ids()

    # Act
    slots = build_handover_slots(unit_ids)

    # Assert
    assert len(slots) == UNIT_COUNT * (len(BATCH_CODES) + 1)


def test_matrix_contains_every_unit_in_every_batch_exactly_once() -> None:
    # Arrange
    unit_ids = _unit_ids()

    # Act
    slots = build_handover_slots(unit_ids)

    # Assert
    for batch_code in (*BATCH_CODES, OVERALL_BATCH_CODE):
        units_in_batch = [slot.unit_id for slot in slots if slot.batch_code == batch_code]
        assert sorted(units_in_batch) == sorted(unit_ids)


def test_matrix_rejects_duplicate_unit_ids() -> None:
    # Arrange
    unit_ids = ["unit-01", "unit-01"]

    # Act / Assert
    with pytest.raises(DeliveryMatrixError, match="Trùng mã đơn vị"):
        build_handover_slots(unit_ids)


def test_matrix_rejects_empty_unit_list() -> None:
    # Arrange / Act / Assert
    with pytest.raises(DeliveryMatrixError, match="Chưa có đơn vị"):
        build_handover_slots([])


def test_status_moves_from_scheduled_to_in_transit() -> None:
    # Arrange / Act
    next_status = change_delivery_status(STATUS_SCHEDULED, STATUS_IN_TRANSIT)

    # Assert
    assert next_status == STATUS_IN_TRANSIT


def test_status_cannot_skip_from_scheduled_to_installed() -> None:
    # Arrange / Act / Assert
    with pytest.raises(DeliveryTransitionError, match="Không thể chuyển"):
        change_delivery_status(STATUS_SCHEDULED, STATUS_INSTALLED)


def test_status_can_be_signed_after_installation() -> None:
    # Arrange / Act
    next_status = change_delivery_status(STATUS_INSTALLED, STATUS_SIGNED_HANDOVER)

    # Assert
    assert next_status == STATUS_SIGNED_HANDOVER


def test_issue_can_be_reported_during_installation() -> None:
    # Arrange / Act
    next_status = change_delivery_status(STATUS_INSTALLED, STATUS_ISSUE_REPORTED)

    # Assert
    assert next_status == STATUS_ISSUE_REPORTED


def test_issue_can_be_resolved_back_to_installed() -> None:
    # Arrange / Act
    next_status = change_delivery_status(STATUS_ISSUE_REPORTED, STATUS_INSTALLED)

    # Assert
    assert next_status == STATUS_INSTALLED


def test_signed_handover_cannot_return_to_scheduled() -> None:
    # Arrange / Act / Assert
    with pytest.raises(DeliveryTransitionError):
        change_delivery_status(STATUS_SIGNED_HANDOVER, STATUS_SCHEDULED)
