"""Sinh mã CR/NCR/rủi ro: `{mã dự án}-{LOẠI}-{SỐ 3 chữ số}`, số tăng theo từng LOẠI trong dự án."""

from collections.abc import Iterable

from app.models.risk_issue import RecordType

SEQUENCE_WIDTH = 3


def record_prefix(project_code: str, record_type: RecordType) -> str:
    return f"{project_code}-{record_type.value}-"


def build_record_code(project_code: str, record_type: RecordType, sequence: int) -> str:
    return f"{record_prefix(project_code, record_type)}{sequence:0{SEQUENCE_WIDTH}d}"


def next_sequence(existing_codes: Iterable[str], prefix: str) -> int:
    """Số kế tiếp sau số lớn nhất đang có cùng tiền tố; bỏ qua mã không đúng dạng số."""
    numbers = [
        int(code[len(prefix) :])
        for code in existing_codes
        if code.startswith(prefix) and code[len(prefix) :].isdigit()
    ]
    return max(numbers, default=0) + 1
