import pytest

from app.core.project_health import (
    DEFAULT_HEALTH_THRESHOLDS,
    HealthThresholds,
    ProjectHealthInputs,
    derive_project_health,
)
from app.models.project import ProjectHealth

pytestmark = pytest.mark.unit


def _inputs(
    *,
    is_completed: bool = False,
    hard_deadline_late: bool = False,
    max_slippage_days: int = 0,
    red_alert_count: int = 0,
) -> ProjectHealthInputs:
    return ProjectHealthInputs(
        is_completed=is_completed,
        hard_deadline_late=hard_deadline_late,
        max_slippage_days=max_slippage_days,
        red_alert_count=red_alert_count,
    )


def test_completed_project_is_completed_even_with_alerts() -> None:
    # Arrange
    inputs = _inputs(is_completed=True, max_slippage_days=30, red_alert_count=9)

    # Act
    health = derive_project_health(inputs, DEFAULT_HEALTH_THRESHOLDS)

    # Assert
    assert health == ProjectHealth.COMPLETED


def test_late_hard_deadline_is_critical() -> None:
    # Arrange
    inputs = _inputs(hard_deadline_late=True, max_slippage_days=1)

    # Act
    health = derive_project_health(inputs, DEFAULT_HEALTH_THRESHOLDS)

    # Assert
    assert health == ProjectHealth.CRITICAL


def test_more_than_three_red_alerts_is_critical() -> None:
    # Arrange
    inputs = _inputs(red_alert_count=4)

    # Act
    health = derive_project_health(inputs, DEFAULT_HEALTH_THRESHOLDS)

    # Assert
    assert health == ProjectHealth.CRITICAL


def test_exactly_three_red_alerts_is_not_critical() -> None:
    # Arrange
    inputs = _inputs(red_alert_count=3)

    # Act
    health = derive_project_health(inputs, DEFAULT_HEALTH_THRESHOLDS)

    # Assert
    assert health == ProjectHealth.AT_RISK


def test_slippage_over_seven_days_is_delayed() -> None:
    # Arrange
    inputs = _inputs(max_slippage_days=8)

    # Act
    health = derive_project_health(inputs, DEFAULT_HEALTH_THRESHOLDS)

    # Assert
    assert health == ProjectHealth.DELAYED


def test_slippage_of_exactly_seven_days_is_at_risk() -> None:
    # Arrange
    inputs = _inputs(max_slippage_days=7)

    # Act
    health = derive_project_health(inputs, DEFAULT_HEALTH_THRESHOLDS)

    # Assert
    assert health == ProjectHealth.AT_RISK


def test_one_red_alert_without_slippage_is_at_risk() -> None:
    # Arrange
    inputs = _inputs(red_alert_count=1)

    # Act
    health = derive_project_health(inputs, DEFAULT_HEALTH_THRESHOLDS)

    # Assert
    assert health == ProjectHealth.AT_RISK


def test_no_slippage_and_no_alerts_is_on_track() -> None:
    # Arrange
    inputs = _inputs()

    # Act
    health = derive_project_health(inputs, DEFAULT_HEALTH_THRESHOLDS)

    # Assert
    assert health == ProjectHealth.ON_TRACK


def test_custom_thresholds_change_the_result() -> None:
    # Arrange
    strict = HealthThresholds(delayed_slippage_days=2, critical_red_alert_count=0)
    inputs = _inputs(max_slippage_days=3)

    # Act
    health = derive_project_health(inputs, strict)

    # Assert
    assert health == ProjectHealth.DELAYED
