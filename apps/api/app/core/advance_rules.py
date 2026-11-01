"""Quy tắc tạm ứng thuần (không chạm DB): trần tạm ứng và thời hạn ngày làm việc.

Tỷ lệ trần và số ngày làm việc do người gọi truyền vào từ `finance_rules`.
Ngày nghỉ là cấu hình, không hard-code.
"""

from collections.abc import Collection
from datetime import date, timedelta
from decimal import Decimal

from app.core.money import percent_of

SATURDAY_WEEKDAY = 5


def advance_ceiling_amount(contract_value: Decimal, ceiling_percent: Decimal) -> Decimal:
    """Hạn mức tạm ứng tối đa = tỷ lệ trần × giá trị hợp đồng."""
    return percent_of(contract_value, ceiling_percent)


def advance_within_ceiling(
    *,
    contract_value: Decimal,
    ceiling_percent: Decimal,
    already_granted: Decimal,
    requested: Decimal,
) -> bool:
    """Tổng đã tạm ứng cộng khoản mới không vượt trần. Bằng đúng trần vẫn hợp lệ."""
    ceiling = advance_ceiling_amount(contract_value, ceiling_percent)
    return already_granted + requested <= ceiling


def working_days_between(start: date, end: date, non_working_days: Collection[date]) -> int:
    """Số ngày làm việc trong khoảng (start, end]: bỏ thứ Bảy, Chủ nhật và ngày nghỉ cấu hình."""
    if end < start:
        raise ValueError("Ngày kết thúc không được trước ngày bắt đầu")
    count = 0
    current = start
    while current < end:
        current += timedelta(days=1)
        if current.weekday() < SATURDAY_WEEKDAY and current not in non_working_days:
            count += 1
    return count


def is_advance_on_time(
    received_on: date,
    decided_on: date,
    limit_working_days: int,
    non_working_days: Collection[date],
) -> bool:
    """Đúng hạn nếu không quá `limit_working_days` ngày làm việc kể từ khi nhận đủ hồ sơ."""
    return working_days_between(received_on, decided_on, non_working_days) <= limit_working_days
