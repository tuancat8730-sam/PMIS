"""Tiền và phần trăm dùng chung: làm tròn về đồng lẻ 2 chữ số, luôn dùng Decimal."""

from decimal import ROUND_HALF_UP, Decimal

PERCENT_DIVISOR = Decimal("100")
MONEY_QUANTUM = Decimal("0.01")


def percent_of(value: Decimal, percent: Decimal) -> Decimal:
    """`percent`% của `value`, làm tròn nửa lên về 2 chữ số thập phân."""
    return (value * percent / PERCENT_DIVISOR).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)
