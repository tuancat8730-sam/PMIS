from decimal import Decimal

import pytest

from app.core.it_gate_rules import (
    GATED_MILESTONE_CODE,
    is_gated_milestone,
    it_completion_blockers,
)
from app.core.nfr_rules import NfrResult

pytestmark = pytest.mark.unit

PASSED_NFR = (NfrResult(key="ccu", passed=True, measured=Decimal("3700")),)
FAILED_NFR = (NfrResult(key="ccu", passed=False, measured=Decimal("3000")),)


def test_only_m8_is_gated() -> None:
    # Arrange
    other_codes = ("M1", "M7", "M9")

    # Act
    gated = [is_gated_milestone(code) for code in other_codes]

    # Assert
    assert GATED_MILESTONE_CODE == "M8"
    assert gated == [False, False, False]


def test_m8_is_gated() -> None:
    # Arrange
    code = "M8"

    # Act
    gated = is_gated_milestone(code)

    # Assert
    assert gated is True


def test_no_blockers_when_dossier_closed_no_open_serious_pentest_and_nfr_passed() -> None:
    # Arrange
    dossier_closed = True
    open_serious = 0

    # Act
    blockers = it_completion_blockers(dossier_closed, open_serious, PASSED_NFR)

    # Assert
    assert blockers == ()


def test_dossier_not_closed_is_a_blocker() -> None:
    # Arrange
    dossier_closed = False

    # Act
    blockers = it_completion_blockers(dossier_closed, 0, PASSED_NFR)

    # Assert
    assert len(blockers) == 1
    assert "ATTT" in blockers[0]


def test_open_critical_or_high_pentest_findings_are_a_blocker() -> None:
    # Arrange
    open_serious = 2

    # Act
    blockers = it_completion_blockers(True, open_serious, PASSED_NFR)

    # Assert
    assert len(blockers) == 1
    assert "pentest" in blockers[0]
    assert "2" in blockers[0]


def test_failed_nfr_is_a_blocker() -> None:
    # Arrange
    nfr = FAILED_NFR

    # Act
    blockers = it_completion_blockers(True, 0, nfr)

    # Assert
    assert len(blockers) == 1
    assert "NFR" in blockers[0]


def test_all_three_problems_produce_three_blockers() -> None:
    # Arrange
    dossier_closed = False

    # Act
    blockers = it_completion_blockers(dossier_closed, 1, FAILED_NFR)

    # Assert
    assert len(blockers) == 3


def test_empty_nfr_results_is_a_blocker() -> None:
    # Arrange
    nfr: tuple[NfrResult, ...] = ()

    # Act
    blockers = it_completion_blockers(True, 0, nfr)

    # Assert
    assert len(blockers) == 1
    assert "NFR" in blockers[0]
