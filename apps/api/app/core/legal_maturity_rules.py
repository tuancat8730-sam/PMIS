"""Máy trạng thái trưởng thành hồ sơ pháp lý (thuần, không chạm DB).

Chuỗi chuẩn: MISSING → DRAFT_DOCX → SUBMITTED_REVIEW → WAITING_SIGNATURE → SIGNED_SCAN_PDF
→ VERIFIED_CLOSED. DISCREPANCY_FOUND là nhánh phát hiện sai sót, quay lại DRAFT_DOCX để sửa.
VERIFIED_CLOSED khóa: chỉ mở lại được về SIGNED_SCAN_PDF, bắt buộc có lý do.
"""

from collections.abc import Mapping
from types import MappingProxyType

from app.models.legal_document import DocMaturityStatus

S = DocMaturityStatus

# Bước tiến kế tiếp trong chuỗi chuẩn: không bắt buộc lý do.
NEXT_STEP: Mapping[DocMaturityStatus, DocMaturityStatus] = MappingProxyType(
    {
        S.MISSING: S.DRAFT_DOCX,
        S.DRAFT_DOCX: S.SUBMITTED_REVIEW,
        S.SUBMITTED_REVIEW: S.WAITING_SIGNATURE,
        S.WAITING_SIGNATURE: S.SIGNED_SCAN_PDF,
        S.SIGNED_SCAN_PDF: S.VERIFIED_CLOSED,
    }
)

# Chuỗi chuẩn theo thứ tự; dùng để nhận diện đi lùi (bắt buộc lý do).
CHAIN_ORDER: tuple[DocMaturityStatus, ...] = (
    S.MISSING,
    S.DRAFT_DOCX,
    S.SUBMITTED_REVIEW,
    S.WAITING_SIGNATURE,
    S.SIGNED_SCAN_PDF,
    S.VERIFIED_CLOSED,
)

DISCREPANCY_SOURCES: frozenset[DocMaturityStatus] = frozenset(
    {S.SUBMITTED_REVIEW, S.WAITING_SIGNATURE, S.SIGNED_SCAN_PDF}
)
DISCREPANCY_RETURN = S.DRAFT_DOCX
REOPEN_TARGET = S.SIGNED_SCAN_PDF
LOCKED_STATUS = S.VERIFIED_CLOSED


def is_locked(status: DocMaturityStatus) -> bool:
    """Hồ sơ đã đóng không sửa trực tiếp được; chỉ mở lại qua chuyển trạng thái có lý do."""
    return status == LOCKED_STATUS


def _is_next_step(current: DocMaturityStatus, target: DocMaturityStatus) -> bool:
    return NEXT_STEP.get(current) == target


def _is_discrepancy(current: DocMaturityStatus, target: DocMaturityStatus) -> bool:
    return target == S.DISCREPANCY_FOUND and current in DISCREPANCY_SOURCES


def _is_return_from_discrepancy(current: DocMaturityStatus, target: DocMaturityStatus) -> bool:
    return current == S.DISCREPANCY_FOUND and target == DISCREPANCY_RETURN


def _is_reopen(current: DocMaturityStatus, target: DocMaturityStatus) -> bool:
    return current == LOCKED_STATUS and target == REOPEN_TARGET


def _is_backward(current: DocMaturityStatus, target: DocMaturityStatus) -> bool:
    if current not in CHAIN_ORDER or target not in CHAIN_ORDER or is_locked(current):
        return False
    return CHAIN_ORDER.index(target) < CHAIN_ORDER.index(current)


def can_transition(current: DocMaturityStatus, target: DocMaturityStatus) -> bool:
    """Chuyển trạng thái có hợp lệ không; cùng trạng thái, bỏ bước hoặc đang khóa thì không."""
    if current == target:
        return False
    if is_locked(current):
        return _is_reopen(current, target)
    return (
        _is_next_step(current, target)
        or _is_discrepancy(current, target)
        or _is_return_from_discrepancy(current, target)
        or _is_backward(current, target)
    )


def requires_reason(current: DocMaturityStatus, target: DocMaturityStatus) -> bool:
    """Mọi chuyển trạng thái ngoài bước tiến kế tiếp đều phải có lý do và được ghi audit."""
    return not _is_next_step(current, target)
