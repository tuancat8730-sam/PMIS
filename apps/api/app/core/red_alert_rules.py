"""Quy tắc thẻ cảnh báo đỏ: việc đến hạn trong 48 giờ hoặc đã quá hạn (thuần, không chạm DB).

Ở mức ngày, 48 giờ được quy thành `RED_ALERT_WINDOW_DAYS` = 2 ngày lịch.
"""

from datetime import date, timedelta

RED_ALERT_WINDOW_DAYS = 2


def is_red_alert(due: date | None, today: date) -> bool:
    """Đỏ khi hạn không xác định thì không đỏ; quá hạn hoặc còn trong cửa sổ thì đỏ."""
    if due is None:
        return False
    return due <= today + timedelta(days=RED_ALERT_WINDOW_DAYS)
