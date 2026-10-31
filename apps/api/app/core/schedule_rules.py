"""Quy tắc tiến độ thuần (không chạm DB): slippage, phạt có trần, mốc cứng, trạng thái suy ra.

Ngưỡng phạt (tỷ lệ/ngày, trần %) do người gọi truyền vào từ `penalty_rules`, không hard-code ở đây.
"""

from collections.abc import Collection
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from app.models.milestone import MilestoneStatus, StoredMilestoneStatus

PERCENT_DIVISOR = Decimal("100")
MONEY_QUANTUM = Decimal("0.01")
NO_PENALTY = Decimal("0.00")


def effective_due_date(baseline_end: date, adjusted_end: date | None) -> date:
    """Hạn áp dụng để tính trễ: hạn điều chỉnh nếu có, không thì hạn gốc."""
    return adjusted_end if adjusted_end is not None else baseline_end


def slippage_days(due: date, actual_end: date | None, today: date) -> int:
    """Số ngày trễ (âm nếu xong sớm). Mốc chưa xong thì tính đến hôm nay."""
    finish = actual_end if actual_end is not None else today
    return (finish - due).days


def penalty_amount(
    contract_value: Decimal,
    slippage: int,
    rate_per_day: Decimal,
    cap_percent: Decimal,
) -> Decimal:
    """Phạt = giá trị hợp đồng × tỷ lệ/ngày × số ngày trễ, không vượt trần % giá trị hợp đồng."""
    if slippage <= 0:
        return NO_PENALTY
    uncapped = contract_value * rate_per_day * slippage
    cap = contract_value * cap_percent / PERCENT_DIVISOR
    return min(uncapped, cap).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def hard_deadline_respected(
    is_hard_deadline: bool,
    baseline_end: date,
    adjusted_end: date | None,
) -> bool:
    """Mốc cứng không được lùi quá hạn gốc. Mốc thường thì luôn hợp lệ."""
    if not is_hard_deadline or adjusted_end is None:
        return True
    return adjusted_end <= baseline_end


def derive_milestone_status(
    stored: StoredMilestoneStatus,
    baseline_end: date,
    adjusted_end: date | None,
    actual_end: date | None,
    today: date,
) -> MilestoneStatus:
    """Suy ra trạng thái hiển thị. COMPLETED không bao giờ bị ghi đè."""
    if stored == StoredMilestoneStatus.COMPLETED:
        return MilestoneStatus.COMPLETED
    if today > effective_due_date(baseline_end, adjusted_end):
        return MilestoneStatus.OVERDUE
    if adjusted_end is not None and adjusted_end > baseline_end:
        return MilestoneStatus.AT_RISK
    return MilestoneStatus(stored.value)


def missing_confirmation_parties(
    confirmed: Collection[str],
    required: frozenset[str],
) -> frozenset[str]:
    """Các bên chưa xác nhận trong số bên bắt buộc."""
    return required - frozenset(confirmed)
