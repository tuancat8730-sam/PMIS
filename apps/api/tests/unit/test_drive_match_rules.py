from uuid import uuid4

import pytest

from app.core.drive_match_rules import MatchableDocument, suggest_matches

pytestmark = pytest.mark.unit

DECISION_DOC = MatchableDocument(
    document_id=uuid4(),
    doc_code_symbol="1595/QĐ-SGDĐT",
    doc_name="Quyết định phê duyệt chủ trương đầu tư",
)
NAME_ONLY_DOC = MatchableDocument(
    document_id=uuid4(),
    doc_code_symbol=None,
    doc_name="Quyết định phê duyệt chủ trương đầu tư",
)


def test_file_containing_document_code_symbol_is_suggested_by_symbol() -> None:
    # Arrange
    files = [("f-1", "1595_QD_SGDDT_chu_truong.pdf")]

    # Act
    suggestions = suggest_matches(files, [DECISION_DOC])

    # Assert
    assert [(s.drive_file_id, s.document_id, s.reason) for s in suggestions] == [
        ("f-1", DECISION_DOC.document_id, "symbol"),
    ]


def test_file_sharing_most_words_with_document_name_is_suggested_by_name() -> None:
    # Arrange
    files = [("f-2", "QD phe duyet chu truong dau tu.pdf")]

    # Act
    suggestions = suggest_matches(files, [NAME_ONLY_DOC])

    # Assert
    assert [(s.drive_file_id, s.reason) for s in suggestions] == [("f-2", "name")]


def test_unrelated_file_gets_no_suggestion() -> None:
    # Arrange
    files = [("f-3", "anh_hien_truong.jpg")]

    # Act
    suggestions = suggest_matches(files, [DECISION_DOC])

    # Assert
    assert suggestions == []


def test_very_short_document_code_does_not_match_by_symbol() -> None:
    # Arrange
    short_doc = MatchableDocument(
        document_id=uuid4(),
        doc_code_symbol="01",
        doc_name="Biên bản",
    )
    files = [("f-4", "bien_ban_01_hop.pdf")]

    # Act
    suggestions = suggest_matches(files, [short_doc])

    # Assert
    assert all(s.reason != "symbol" for s in suggestions)
