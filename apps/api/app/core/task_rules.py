"""Quy tắc task con (thuần, không chạm DB)."""

from datetime import date

from app.models.milestone_task import TaskStatus


def is_task_overdue(status: TaskStatus, due_date: date | None, today: date) -> bool:
    """Task quá hạn khi chưa hoàn thành và hạn đã qua. Hạn là hôm nay thì chưa trễ."""
    if due_date is None or status == TaskStatus.COMPLETED:
        return False
    return due_date < today
