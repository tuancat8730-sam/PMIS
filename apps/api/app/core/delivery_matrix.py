"""Ma trận giao hàng theo đơn vị và đợt, cùng máy trạng thái giao nhận (thuần, không chạm DB).

Mỗi đơn vị có một dòng cho từng đợt (DOT_1..DOT_3) cộng một dòng TONG_THE.
Bảng chuyển trạng thái dưới đây là GIẢ ĐỊNH của đội phát triển,
chưa được người dùng chốt (plan E9, C4).
"""

from collections.abc import Sequence
from dataclasses import dataclass

BATCH_CODES: tuple[str, ...] = ("DOT_1", "DOT_2", "DOT_3")
OVERALL_BATCH_CODE = "TONG_THE"

STATUS_SCHEDULED = "SCHEDULED"
STATUS_IN_TRANSIT = "IN_TRANSIT"
STATUS_INSTALLED = "INSTALLED"
STATUS_SIGNED_HANDOVER = "SIGNED_HANDOVER"
STATUS_ISSUE_REPORTED = "ISSUE_REPORTED"

_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    STATUS_SCHEDULED: frozenset({STATUS_IN_TRANSIT}),
    STATUS_IN_TRANSIT: frozenset({STATUS_INSTALLED, STATUS_ISSUE_REPORTED}),
    STATUS_INSTALLED: frozenset({STATUS_SIGNED_HANDOVER, STATUS_ISSUE_REPORTED}),
    STATUS_SIGNED_HANDOVER: frozenset({STATUS_ISSUE_REPORTED}),
    STATUS_ISSUE_REPORTED: frozenset({STATUS_INSTALLED}),
}


class DeliveryMatrixError(Exception):
    """Dữ liệu đầu vào của ma trận không hợp lệ: rỗng hoặc trùng mã đơn vị."""


class DeliveryTransitionError(Exception):
    """Chuyển trạng thái giao nhận không nằm trong bảng cho phép."""


@dataclass(frozen=True)
class HandoverSlot:
    unit_id: str
    batch_code: str


def build_handover_slots(unit_ids: Sequence[str]) -> tuple[HandoverSlot, ...]:
    """Sinh mọi cặp (đơn vị, đợt) kể cả dòng tổng thể: số dòng = số đơn vị × (số đợt + 1)."""
    if not unit_ids:
        raise DeliveryMatrixError("Chưa có đơn vị để lập ma trận giao hàng")
    if len(set(unit_ids)) != len(unit_ids):
        raise DeliveryMatrixError("Trùng mã đơn vị trong ma trận giao hàng")
    batch_codes = (*BATCH_CODES, OVERALL_BATCH_CODE)
    return tuple(
        HandoverSlot(unit_id=unit_id, batch_code=batch_code)
        for batch_code in batch_codes
        for unit_id in unit_ids
    )


def change_delivery_status(current: str, target: str) -> str:
    """Trả về trạng thái mới nếu chuyển đổi được phép, ngược lại báo lỗi."""
    allowed = _ALLOWED_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise DeliveryTransitionError(f"Không thể chuyển từ {current} sang {target}")
    return target
