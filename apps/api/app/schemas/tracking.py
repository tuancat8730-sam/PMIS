from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.risk_matrix_rules import risk_score
from app.models.risk_issue import RecordType, RiskIssue, RiskLevel, RiskStatus
from app.schemas.milestones import MilestoneOut


class ScheduleMatrixOut(BaseModel):
    total: int
    rows: list[MilestoneOut]


class RiskMatrixRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    record_type: RecordType
    title: str
    status: RiskStatus
    owner: str | None
    due_date: date | None
    impact: RiskLevel | None
    likelihood: RiskLevel | None
    score: int | None
    coordinating_units: str | None

    @classmethod
    def from_risk(cls, risk: RiskIssue) -> "RiskMatrixRow":
        return cls(
            id=risk.id,
            code=risk.code,
            record_type=risk.record_type,
            title=risk.title,
            status=risk.status,
            owner=risk.owner,
            due_date=risk.due_date,
            impact=risk.impact,
            likelihood=risk.likelihood,
            score=risk_score(risk.impact, risk.likelihood),
            coordinating_units=risk.coordinating_units,
        )


class RiskMatrixOut(BaseModel):
    total: int
    rows: list[RiskMatrixRow]
