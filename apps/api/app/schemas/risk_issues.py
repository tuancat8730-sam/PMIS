from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.risk_issue import (
    CATEGORY_MAX_LENGTH,
    OWNER_MAX_LENGTH,
    STAKEHOLDER_MAX_LENGTH,
    RecordType,
    RiskPriority,
    RiskStatus,
)
from app.schemas.base import RequestModel

TITLE_MAX_LENGTH = 300
DESCRIPTION_MAX_LENGTH = 4000
MITIGATION_MAX_LENGTH = 2000
RESOLUTION_REF_MAX_LENGTH = 300


class RiskIssueCreate(RequestModel):
    record_type: RecordType
    title: str = Field(min_length=1, max_length=TITLE_MAX_LENGTH)
    description: str = Field(min_length=1, max_length=DESCRIPTION_MAX_LENGTH)
    category: str | None = Field(default=None, max_length=CATEGORY_MAX_LENGTH)
    priority: RiskPriority = RiskPriority.HIGH
    target_stakeholder: str | None = Field(default=None, max_length=STAKEHOLDER_MAX_LENGTH)
    mitigation_action: str | None = Field(default=None, max_length=MITIGATION_MAX_LENGTH)
    owner: str | None = Field(default=None, max_length=OWNER_MAX_LENGTH)
    due_date: date | None = None


class RiskIssueUpdate(RequestModel):
    status: RiskStatus | None = None
    priority: RiskPriority | None = None
    mitigation_action: str | None = Field(default=None, max_length=MITIGATION_MAX_LENGTH)
    owner: str | None = Field(default=None, max_length=OWNER_MAX_LENGTH)
    due_date: date | None = None
    resolution_ref: str | None = Field(default=None, max_length=RESOLUTION_REF_MAX_LENGTH)

    @model_validator(mode="after")
    def _reject_null_for_required_fields(self) -> "RiskIssueUpdate":
        for field_name in ("status", "priority"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} không được để trống")
        return self


class RiskIssueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    record_type: RecordType
    code: str
    category: str | None
    title: str
    description: str
    priority: RiskPriority
    status: RiskStatus
    target_stakeholder: str | None
    mitigation_action: str | None
    owner: str | None
    due_date: date | None
    resolution_ref: str | None
    created_at: datetime
