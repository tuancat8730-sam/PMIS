from datetime import date

import pytest

from app.core.task_rules import is_task_overdue
from app.models.milestone_task import TaskStatus

pytestmark = pytest.mark.unit

TODAY = date(2026, 11, 15)


def test_open_task_past_due_date_is_overdue() -> None:
    # Arrange
    status = TaskStatus.IN_PROGRESS
    due_date = date(2026, 11, 10)

    # Act
    result = is_task_overdue(status, due_date, TODAY)

    # Assert
    assert result is True


def test_completed_task_past_due_date_is_not_overdue() -> None:
    # Arrange
    status = TaskStatus.COMPLETED
    due_date = date(2026, 11, 10)

    # Act
    result = is_task_overdue(status, due_date, TODAY)

    # Assert
    assert result is False


def test_task_due_today_is_not_overdue() -> None:
    # Arrange
    status = TaskStatus.NOT_STARTED
    due_date = TODAY

    # Act
    result = is_task_overdue(status, due_date, TODAY)

    # Assert
    assert result is False


def test_task_without_due_date_is_not_overdue() -> None:
    # Arrange
    status = TaskStatus.NOT_STARTED

    # Act
    result = is_task_overdue(status, None, TODAY)

    # Assert
    assert result is False
