"""Quy tắc đóng mâu thuẫn hợp đồng (thuần): mâu thuẫn Phụ lục C chỉ đóng khi có văn bản chốt CĐT.

Mâu thuẫn được lưu trong `risk_issues` với loại CONTRACT_DISCREPANCY (E3), không tạo bảng riêng.
"""

from app.models.risk_issue import RecordType, RiskStatus

CLOSING_STATUSES: frozenset[RiskStatus] = frozenset({RiskStatus.RESOLVED, RiskStatus.CLOSED})


def closing_requires_resolution(
    record_type: RecordType,
    target_status: RiskStatus,
    resolution_ref: str | None,
) -> bool:
    """True khi thao tác đóng bị chặn: mâu thuẫn hợp đồng cần văn bản chốt mà chưa có."""
    if record_type is not RecordType.CONTRACT_DISCREPANCY:
        return False
    if target_status not in CLOSING_STATUSES:
        return False
    return resolution_ref is None or resolution_ref.strip() == ""
