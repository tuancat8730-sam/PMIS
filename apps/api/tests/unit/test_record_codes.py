import pytest

from app.core.record_codes import build_record_code, next_sequence
from app.models.risk_issue import RecordType

pytestmark = pytest.mark.unit


def test_build_record_code_joins_project_code_type_and_padded_sequence() -> None:
    # Arrange
    project_code = "SGD-HCM-CSVC-2026"

    # Act
    code = build_record_code(project_code, RecordType.NCR, 1)

    # Assert
    assert code == "SGD-HCM-CSVC-2026-NCR-001"


def test_next_sequence_starts_at_one_when_no_codes_exist() -> None:
    # Arrange
    prefix = "SGD-HCM-CSVC-2026-CR-"

    # Act
    sequence = next_sequence([], prefix)

    # Assert
    assert sequence == 1


def test_next_sequence_follows_highest_existing_number_for_the_same_prefix() -> None:
    # Arrange
    prefix = "SGD-HCM-CSVC-2026-NCR-"
    existing = ["SGD-HCM-CSVC-2026-NCR-001", "SGD-HCM-CSVC-2026-NCR-002"]

    # Act
    sequence = next_sequence(existing, prefix)

    # Assert
    assert sequence == 3


def test_next_sequence_ignores_codes_of_other_record_types() -> None:
    # Arrange
    prefix = "SGD-HCM-CSVC-2026-CR-"
    existing = ["SGD-HCM-CSVC-2026-NCR-009", "SGD-HCM-CSVC-2026-CR-002"]

    # Act
    sequence = next_sequence(existing, prefix)

    # Assert
    assert sequence == 3
