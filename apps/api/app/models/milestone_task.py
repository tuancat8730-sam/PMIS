import uuid
from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.project import enum_values

TASK_NAME_MAX_LENGTH = 300
TASK_ASSIGNEE_MAX_LENGTH = 300
TASK_NOTE_MAX_LENGTH = 2000


class TaskStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class MilestoneTask(Base):
    """Task con của một mốc tiến độ. Đổi trạng thái task không tự đổi % hoàn thành của mốc."""

    __tablename__ = "milestone_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    milestone_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("milestones_wbs.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(TASK_NAME_MAX_LENGTH))
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="milestone_task_status", values_callable=enum_values),
        default=TaskStatus.NOT_STARTED,
        server_default=text("'NOT_STARTED'"),
    )
    assignee: Mapped[str | None] = mapped_column(String(TASK_ASSIGNEE_MAX_LENGTH), default=None)
    due_date: Mapped[date | None] = mapped_column(Date, default=None)
    note: Mapped[str | None] = mapped_column(Text, default=None)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
