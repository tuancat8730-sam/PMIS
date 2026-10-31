from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.core.schedule_rules import derive_milestone_status, effective_due_date, slippage_days
from app.models.milestone import (
    MILESTONE_CODE_MAX_LENGTH,
    Milestone,
    MilestoneStatus,
    StoredMilestoneStatus,
)
from app.schemas.base import RequestModel

MILESTONE_NAME_MAX_LENGTH = 300
RESPONSIBLE_PARTY_MAX_LENGTH = 300
EVIDENCE_SUMMARY_MAX_LENGTH = 2000
REASON_MAX_LENGTH = 1000
PERCENT_MIN = Decimal("0")
PERCENT_MAX = Decimal("100")


class MilestoneCreate(RequestModel):
    code: str = Field(min_length=1, max_length=MILESTONE_CODE_MAX_LENGTH, pattern=r"^\S+$")
    name: str = Field(min_length=1, max_length=MILESTONE_NAME_MAX_LENGTH)
    baseline_start: date | None = None
    baseline_end: date
    adjusted_start: date | None = None
    adjusted_end: date | None = None
    is_hard_deadline: bool = False
    responsible_party: str | None = Field(default=None, max_length=RESPONSIBLE_PARTY_MAX_LENGTH)
    evidence_summary: str | None = Field(default=None, max_length=EVIDENCE_SUMMARY_MAX_LENGTH)


class MilestoneUpdate(RequestModel):
    adjusted_start: date | None = None
    adjusted_end: date | None = None
    actual_end: date | None = None
    progress_percent: Decimal | None = Field(default=None, ge=PERCENT_MIN, le=PERCENT_MAX)
    status: StoredMilestoneStatus | None = None
    reason: str | None = Field(default=None, min_length=1, max_length=REASON_MAX_LENGTH)

    @model_validator(mode="after")
    def _reject_null_for_required_fields(self) -> "MilestoneUpdate":
        for field_name in ("progress_percent", "status"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} không được để trống")
        return self


class MilestoneOut(BaseModel):
    id: UUID
    project_id: UUID
    code: str
    name: str
    baseline_start: date | None
    baseline_end: date
    adjusted_start: date | None
    adjusted_end: date | None
    actual_end: date | None
    is_hard_deadline: bool
    progress_percent: Decimal
    status: StoredMilestoneStatus
    display_status: MilestoneStatus
    slippage_days: int
    responsible_party: str | None
    evidence_summary: str | None

    @classmethod
    def from_milestone(cls, milestone: Milestone, today: date) -> "MilestoneOut":
        due = effective_due_date(milestone.baseline_end, milestone.adjusted_end)
        return cls(
            id=milestone.id,
            project_id=milestone.project_id,
            code=milestone.code,
            name=milestone.name,
            baseline_start=milestone.baseline_start,
            baseline_end=milestone.baseline_end,
            adjusted_start=milestone.adjusted_start,
            adjusted_end=milestone.adjusted_end,
            actual_end=milestone.actual_end,
            is_hard_deadline=milestone.is_hard_deadline,
            progress_percent=milestone.progress_percent,
            status=milestone.status,
            display_status=derive_milestone_status(
                milestone.status,
                milestone.baseline_end,
                milestone.adjusted_end,
                milestone.actual_end,
                today,
            ),
            slippage_days=slippage_days(due, milestone.actual_end, today),
            responsible_party=milestone.responsible_party,
            evidence_summary=milestone.evidence_summary,
        )
