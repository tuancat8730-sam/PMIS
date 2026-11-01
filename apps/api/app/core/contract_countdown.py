"""Đếm ngược hết hạn hợp đồng (thuần, không chạm DB)."""

from datetime import date
from enum import StrEnum

DEFAULT_COUNTDOWN_WARNING_DAYS = 30


class CountdownStatus(StrEnum):
    NO_DATE = "NO_DATE"
    EXPIRED = "EXPIRED"
    WARNING = "WARNING"
    OK = "OK"


def days_until_expiration(expiration: date, today: date) -> int:
    """Số ngày lịch còn lại. Âm nghĩa là đã hết hạn."""
    return (expiration - today).days


def countdown_status(
    expiration: date | None,
    today: date,
    warning_days: int = DEFAULT_COUNTDOWN_WARNING_DAYS,
) -> CountdownStatus:
    """Cảnh báo khi còn không quá `warning_days` ngày; đã hết hạn thì tách riêng."""
    if expiration is None:
        return CountdownStatus.NO_DATE
    remaining = days_until_expiration(expiration, today)
    if remaining < 0:
        return CountdownStatus.EXPIRED
    if remaining <= warning_days:
        return CountdownStatus.WARNING
    return CountdownStatus.OK
