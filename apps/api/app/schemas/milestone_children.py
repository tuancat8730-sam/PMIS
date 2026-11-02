from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.core.task_rules import is_task_overdue
from app.models.milestone_note import MilestoneNote
from app.models.milestone_task import (
    TASK_ASSIGNEE_MAX_LENGTH,
    TASK_NAME_MAX_LENGTH,
    TASK_NOTE_MAX_LENGTH,
    MilestoneTask,
    TaskStatus,
)
from app.schemas.base import RequestModel

NOTE_BODY_MAX_LENGTH = 2000


class TaskCreate(RequestModel):
    name: str = Field(min_length=1, max_length=TASK_NAME_MAX_LENGTH)
    status: TaskStatus = TaskStatus.NOT_STARTED
    assignee: str | None = Field(default=None, max_length=TASK_ASSIGNEE_MAX_LENGTH)
    due_date: date | None = None
    note: str | None = Field(default=None, max_length=TASK_NOTE_MAX_LENGTH)


class TaskUpdate(RequestModel):
    name: str | None = Field(default=None, min_length=1, max_length=TASK_NAME_MAX_LENGTH)
    status: TaskStatus | None = None
    assignee: str | None = Field(default=None, max_length=TASK_ASSIGNEE_MAX_LENGTH)
    due_date: date | None = None
    note: str | None = Field(default=None, max_length=TASK_NOTE_MAX_LENGTH)

    @model_validator(mode="after")
    def _reject_null_for_required_fields(self) -> "TaskUpdate":
        for field_name in ("name", "status"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} không được để trống")
        return self


class TaskOut(BaseModel):
    id: UUID
    milestone_id: UUID
    name: str
    status: TaskStatus
    assignee: str | None
    due_date: date | None
    note: str | None
    is_overdue: bool

    @classmethod
    def from_task(cls, task: MilestoneTask, today: date) -> "TaskOut":
        return cls(
            id=task.id,
            milestone_id=task.milestone_id,
            name=task.name,
            status=task.status,
            assignee=task.assignee,
            due_date=task.due_date,
            note=task.note,
            is_overdue=is_task_overdue(task.status, task.due_date, today),
        )


class NoteCreate(RequestModel):
    body: str = Field(min_length=1, max_length=NOTE_BODY_MAX_LENGTH)


class NoteOut(BaseModel):
    id: UUID
    milestone_id: UUID
    body: str
    created_by: UUID
    created_at: datetime

    @classmethod
    def from_note(cls, note: MilestoneNote) -> "NoteOut":
        return cls(
            id=note.id,
            milestone_id=note.milestone_id,
            body=note.body,
            created_by=note.created_by,
            created_at=note.created_at,
        )
