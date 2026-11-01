"""Trạng thái dùng chung của module CNTT (E8). Lưu dạng chuỗi UPPER_SNAKE trong DB."""

from enum import StrEnum


class SurveyStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class QaStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    PASSED = "PASSED"
    FAILED = "FAILED"


class PentestSeverity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PentestFixStatus(StrEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    FIXED = "FIXED"
    VERIFIED = "VERIFIED"


# Lỗi "chưa vá" là lỗi chưa đạt FIXED; chỉ hai trạng thái này được coi là còn mở.
UNRESOLVED_FIX_STATUSES: frozenset[PentestFixStatus] = frozenset(
    {PentestFixStatus.OPEN, PentestFixStatus.IN_PROGRESS}
)
# Mức nghiêm trọng chặn nghiệm thu khi còn mở (Q6).
BLOCKING_SEVERITIES: frozenset[PentestSeverity] = frozenset(
    {PentestSeverity.CRITICAL, PentestSeverity.HIGH}
)
