"""Quy tắc sức khỏe dự án (thuần, không chạm DB).

Ngưỡng là tham số có giá trị mặc định theo đề xuất Q3 của E12. Đổi ngưỡng không cần sửa logic.
"""

from dataclasses import dataclass

from app.models.project import ProjectHealth

DEFAULT_DELAYED_SLIPPAGE_DAYS = 7
DEFAULT_CRITICAL_RED_ALERT_COUNT = 3


@dataclass(frozen=True)
class HealthThresholds:
    delayed_slippage_days: int = DEFAULT_DELAYED_SLIPPAGE_DAYS
    critical_red_alert_count: int = DEFAULT_CRITICAL_RED_ALERT_COUNT


DEFAULT_HEALTH_THRESHOLDS = HealthThresholds()


@dataclass(frozen=True)
class ProjectHealthInputs:
    is_completed: bool
    hard_deadline_late: bool
    max_slippage_days: int
    red_alert_count: int


def derive_project_health(
    inputs: ProjectHealthInputs,
    thresholds: HealthThresholds,
) -> ProjectHealth:
    """Suy ra sức khỏe theo thứ tự ưu tiên: COMPLETED, CRITICAL, DELAYED, AT_RISK, ON_TRACK."""
    if inputs.is_completed:
        return ProjectHealth.COMPLETED
    if inputs.hard_deadline_late or inputs.red_alert_count > thresholds.critical_red_alert_count:
        return ProjectHealth.CRITICAL
    if inputs.max_slippage_days > thresholds.delayed_slippage_days:
        return ProjectHealth.DELAYED
    if inputs.max_slippage_days > 0 or inputs.red_alert_count > 0:
        return ProjectHealth.AT_RISK
    return ProjectHealth.ON_TRACK
