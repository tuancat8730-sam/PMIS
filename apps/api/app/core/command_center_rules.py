"""Quy tắc tổng hợp cho Command Center (thuần, không chạm DB).

Nhận dữ liệu đã đọc từ DB dưới dạng giá trị bất biến và trả về số liệu đã suy ra.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.core.project_health import ProjectHealthInputs
from app.core.red_alert_rules import is_red_alert
from app.core.schedule_rules import effective_due_date, slippage_days

PACKAGE_KINDS = ("MAIN", "CONSULTING")


@dataclass(frozen=True)
class MilestoneTiming:
    baseline_end: date
    adjusted_end: date | None
    actual_end: date | None
    is_hard_deadline: bool


def _due(milestone: MilestoneTiming) -> date:
    return effective_due_date(milestone.baseline_end, milestone.adjusted_end)


def _slippage(milestone: MilestoneTiming, today: date) -> int:
    return slippage_days(_due(milestone), milestone.actual_end, today)


def build_health_inputs(
    milestones: Sequence[MilestoneTiming],
    *,
    red_alert_count: int,
    is_completed: bool,
    today: date,
) -> ProjectHealthInputs:
    """Gom số liệu mốc thành đầu vào cho quy tắc sức khỏe. Trễ âm (xong sớm) không tính."""
    slippages = [_slippage(milestone, today) for milestone in milestones]
    hard_deadline_late = any(
        milestone.is_hard_deadline and slip > 0
        for milestone, slip in zip(milestones, slippages, strict=True)
    )
    return ProjectHealthInputs(
        is_completed=is_completed,
        hard_deadline_late=hard_deadline_late,
        max_slippage_days=max((0, *slippages)),
        red_alert_count=red_alert_count,
    )


def is_red_milestone(milestone: MilestoneTiming, today: date) -> bool:
    """Mốc chưa xong mà hạn nằm trong cửa sổ 48 giờ hoặc đã quá hạn."""
    return milestone.actual_end is None and is_red_alert(_due(milestone), today)


def sum_contract_values_by_kind(
    contracts: Iterable[tuple[str, Decimal]],
) -> dict[str, Decimal]:
    """Cộng giá trị hợp đồng theo loại gói. Gói không có hợp đồng nào thì trả về 0."""
    rows = tuple(contracts)
    return {
        kind: sum((value for row_kind, value in rows if row_kind == kind), Decimal("0"))
        for kind in PACKAGE_KINDS
    }
