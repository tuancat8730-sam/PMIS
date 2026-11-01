"""Quy tắc bảo lãnh thực hiện hợp đồng thuần (không chạm DB).

Tỷ lệ bảo lãnh do người gọi truyền vào từ cấu hình `finance_rules`, không hard-code ở đây.
"""

from datetime import date
from decimal import Decimal

from app.core.money import percent_of


def guarantee_amount(contract_value: Decimal, percent: Decimal) -> Decimal:
    """Số tiền bảo lãnh = tỷ lệ × giá trị hợp đồng gốc."""
    return percent_of(contract_value, percent)


def guarantee_is_expired(expires_on: date, on: date) -> bool:
    """Bảo lãnh còn hiệu lực đến hết ngày `expires_on`, hết hạn từ ngày kế tiếp."""
    return on > expires_on


def poa_expired_before_issue(issued_on: date, poa_expires_on: date) -> bool:
    """Giấy ủy quyền của ngân hàng hết hạn trước ngày phát hành bảo lãnh là không hợp lệ."""
    return poa_expires_on < issued_on
