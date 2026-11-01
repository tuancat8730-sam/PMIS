"""Kỳ báo cáo tuần (thuần, không chạm DB): từ Thứ Hai đến Chủ nhật (G1 của E11)."""

from dataclasses import dataclass
from datetime import date, timedelta

PERIOD_LENGTH_DAYS = 6


@dataclass(frozen=True)
class ReportPeriod:
    start: date
    end: date


def week_period_containing(day: date) -> ReportPeriod:
    """Kỳ tuần chứa `day`: Thứ Hai (weekday 0) đến Chủ nhật (weekday 6)."""
    start = day - timedelta(days=day.weekday())
    return ReportPeriod(start=start, end=start + timedelta(days=PERIOD_LENGTH_DAYS))
