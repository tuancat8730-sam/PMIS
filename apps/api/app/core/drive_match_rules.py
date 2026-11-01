"""Gợi ý khớp file Drive với đầu mục checklist pháp lý (thuần, không đổi dữ liệu).

Hai quy tắc, theo thứ tự ưu tiên:
1. `symbol`: số hiệu văn bản (ví dụ `1595/QĐ-SGDĐT`) xuất hiện trong tên file.
2. `name`: đủ tỷ lệ từ trong tên văn bản xuất hiện trong tên file.

Kết quả chỉ là gợi ý để PM xác nhận, không thay đổi `maturity_status`.
"""

import re
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from uuid import UUID

MIN_SYMBOL_LENGTH = 3
MIN_TOKEN_LENGTH = 3
NAME_OVERLAP_THRESHOLD = 0.6
REASON_SYMBOL = "symbol"
REASON_NAME = "name"

_NON_ALPHANUMERIC = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class MatchableDocument:
    document_id: UUID
    doc_code_symbol: str | None
    doc_name: str


@dataclass(frozen=True)
class DriveMatchSuggestion:
    drive_file_id: str
    document_id: UUID
    reason: str


def normalize(text: str) -> str:
    """Bỏ dấu tiếng Việt, đổi `đ` thành `d`, chỉ giữ chữ và số thường, cách nhau bằng dấu cách."""
    decomposed = unicodedata.normalize("NFKD", text.replace("đ", "d").replace("Đ", "D"))
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return _NON_ALPHANUMERIC.sub(" ", without_marks.lower()).strip()


def suggest_matches(
    files: Iterable[tuple[str, str]],
    documents: Sequence[MatchableDocument],
) -> list[DriveMatchSuggestion]:
    """Trả về mọi cặp (file, đầu mục) khớp. `files` là các cặp (id, tên file)."""
    suggestions: list[DriveMatchSuggestion] = []
    for drive_file_id, file_name in files:
        for document in documents:
            reason = _match_reason(file_name, document)
            if reason is not None:
                suggestions.append(
                    DriveMatchSuggestion(
                        drive_file_id=drive_file_id,
                        document_id=document.document_id,
                        reason=reason,
                    )
                )
    return suggestions


def _match_reason(file_name: str, document: MatchableDocument) -> str | None:
    if _contains_symbol(file_name, document.doc_code_symbol):
        return REASON_SYMBOL
    if _name_overlap(file_name, document.doc_name) >= NAME_OVERLAP_THRESHOLD:
        return REASON_NAME
    return None


def _contains_symbol(file_name: str, doc_code_symbol: str | None) -> bool:
    if doc_code_symbol is None:
        return False
    compact_symbol = normalize(doc_code_symbol).replace(" ", "")
    if len(compact_symbol) < MIN_SYMBOL_LENGTH:
        return False
    return compact_symbol in normalize(file_name).replace(" ", "")


def _name_overlap(file_name: str, doc_name: str) -> float:
    document_tokens = _tokens(doc_name)
    if not document_tokens:
        return 0.0
    shared = document_tokens & _tokens(file_name)
    return len(shared) / len(document_tokens)


def _tokens(text: str) -> set[str]:
    return {token for token in normalize(text).split() if len(token) >= MIN_TOKEN_LENGTH}
