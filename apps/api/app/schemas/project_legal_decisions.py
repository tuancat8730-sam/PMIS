from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.project_legal_decision import (
    DECISION_NO_MAX_LENGTH,
    ISSUING_AUTHORITY_MAX_LENGTH,
    LegalDecisionKind,
)
from app.schemas.base import RequestModel

TEXT_MAX_LENGTH = 4000


class ProjectLegalDecisionCreate(RequestModel):
    """Dòng quyết định dùng khi nạp seed; chưa có API ghi."""

    kind: LegalDecisionKind
    decision_no: str = Field(min_length=1, max_length=DECISION_NO_MAX_LENGTH)
    decision_date: date | None = None
    issuing_authority: str | None = Field(default=None, max_length=ISSUING_AUTHORITY_MAX_LENGTH)
    amount: Decimal | None = Field(default=None, ge=0)
    funding_source: str | None = Field(default=None, max_length=TEXT_MAX_LENGTH)
    execution_period: str | None = Field(default=None, max_length=TEXT_MAX_LENGTH)
    note: str | None = Field(default=None, max_length=TEXT_MAX_LENGTH)


class ProjectLegalDecisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    kind: LegalDecisionKind
    decision_no: str
    decision_date: date | None
    issuing_authority: str | None
    amount: Decimal | None
    funding_source: str | None
    execution_period: str | None
    note: str | None
