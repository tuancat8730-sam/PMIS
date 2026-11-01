"""Quy tắc giải ngân thuần (không chạm DB): tỷ lệ giải ngân, đếm ngược và cảnh báo khóa sổ.

Ngày khóa sổ và số ngày cảnh báo do người gọi truyền vào từ `finance_rules`.
"""

from datetime import date
from decimal import Decimal

from app.core.money import MONEY_QUANTUM, PERCENT_DIVISOR

ZERO = Decimal("0")
ZERO_RATE = Decimal("0.00")


def disbursement_rate(paid: Decimal, planned: Decimal) -> Decimal:
    """Tỷ lệ giải ngân (%) = đã giải ngân / kế hoạch vốn năm. Kế hoạch bằng 0 thì tỷ lệ bằng 0."""
    if planned == ZERO:
        return ZERO_RATE
    return (paid * PERCENT_DIVISOR / planned).quantize(MONEY_QUANTUM)


def days_until(target: date, today: date) -> int:
    """Số ngày lịch từ `today` đến `target`. Âm nếu đã qua."""
    return (target - today).days


def lock_warning_active(lock_on: date, today: date, warn_days: int) -> bool:
    """Cảnh báo bật từ `warn_days` ngày trước ngày khóa sổ, đến đúng ngày khóa sổ."""
    remaining = days_until(lock_on, today)
    return 0 <= remaining <= warn_days


def exceeds_plan(paid: Decimal, planned: Decimal) -> bool:
    """Đã giải ngân vượt kế hoạch. Chỉ là cảnh báo, không chặn ghi nhận."""
    return paid > planned
