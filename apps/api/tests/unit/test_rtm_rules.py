import pytest

from app.core.rtm_rules import RtmRow, missing_chain_links, orphan_rows

pytestmark = pytest.mark.unit


def _complete_row(code: str = "PL-C-1") -> RtmRow:
    return RtmRow(
        appendix_c_ref=code,
        srs_ref="SRS-3.2",
        module_code="A",
        test_case_ref="TC-001",
    )


def test_complete_row_has_no_missing_links() -> None:
    # Arrange
    row = _complete_row()

    # Act
    missing = missing_chain_links(row)

    # Assert
    assert missing == frozenset()


def test_row_without_test_case_reports_test_case_link_missing() -> None:
    # Arrange
    row = RtmRow(appendix_c_ref="PL-C-1", srs_ref="SRS-3.2", module_code="A", test_case_ref=None)

    # Act
    missing = missing_chain_links(row)

    # Assert
    assert missing == frozenset({"test_case_ref"})


def test_blank_or_whitespace_link_counts_as_missing() -> None:
    # Arrange
    row = RtmRow(appendix_c_ref="PL-C-1", srs_ref="   ", module_code="", test_case_ref="TC-001")

    # Act
    missing = missing_chain_links(row)

    # Assert
    assert missing == frozenset({"srs_ref", "module_code"})


def test_orphan_rows_returns_only_incomplete_rows_with_their_index() -> None:
    # Arrange
    complete = _complete_row("PL-C-1")
    orphan = RtmRow(appendix_c_ref="PL-C-2", srs_ref=None, module_code="B", test_case_ref=None)
    rows = (complete, orphan)

    # Act
    found = orphan_rows(rows)

    # Assert
    assert found == ((1, frozenset({"srs_ref", "test_case_ref"})),)


def test_orphan_rows_is_empty_when_every_chain_is_complete() -> None:
    # Arrange
    rows = (_complete_row("PL-C-1"), _complete_row("PL-C-2"))

    # Act
    found = orphan_rows(rows)

    # Assert
    assert found == ()
