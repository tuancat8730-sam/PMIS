"""Quy tắc kho serial và CO/CQ (thuần, không chạm DB).

Thiếu hụt = số lượng cần giao − số đã nộp, không âm. Ví dụ đợt 1: 1.420 − 320 = 1.100.
"""

from collections.abc import Iterable

CO_CQ_MISSING = "MISSING"
CO_CQ_PARTIAL = "PARTIAL"
CO_CQ_COMPLETE = "COMPLETE"


class DuplicateSerialError(Exception):
    """File serial có số trùng: từ chối cả file, không nhập một phần."""

    def __init__(self, duplicates: tuple[str, ...]) -> None:
        self.duplicates = duplicates
        listed = ", ".join(duplicates)
        super().__init__(f"Serial bị trùng trong file: {listed}")


def serial_shortage(*, required: int, submitted: int) -> int:
    """Số bộ còn thiếu so với số lượng theo đợt giao; không âm khi nộp dư."""
    return max(required - submitted, 0)


def find_duplicate_serials(serials: Iterable[str]) -> tuple[str, ...]:
    """Serial xuất hiện từ hai lần trở lên, mỗi serial một lần, theo thứ tự gặp đầu tiên."""
    seen: set[str] = set()
    duplicates: list[str] = []
    for raw in serials:
        serial = raw.strip()
        if serial in seen and serial not in duplicates:
            duplicates.append(serial)
        seen.add(serial)
    return tuple(duplicates)


def co_cq_status(*, required: int, attached: int) -> str:
    """Trạng thái CO/CQ theo số bộ đã đính kèm trên tổng số bộ cần."""
    if attached <= 0:
        return CO_CQ_MISSING
    if attached < required:
        return CO_CQ_PARTIAL
    return CO_CQ_COMPLETE
