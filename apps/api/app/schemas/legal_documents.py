from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.legal_document import (
    ASSIGNEE_MAX_LENGTH,
    DOC_CODE_MAX_LENGTH,
    ISSUING_AUTHORITY_MAX_LENGTH,
    DocMaturityStatus,
    LegalPhaseGroup,
)
from app.schemas.base import RequestModel

DOC_NAME_MAX_LENGTH = 1000
ACTION_MAX_LENGTH = 2000
NOTES_MAX_LENGTH = 4000
REASON_MAX_LENGTH = 1000


class LegalDocumentCreate(RequestModel):
    stt: int = Field(ge=1)
    phase_group: LegalPhaseGroup
    doc_code_symbol: str | None = Field(default=None, max_length=DOC_CODE_MAX_LENGTH)
    doc_name: str = Field(min_length=1, max_length=DOC_NAME_MAX_LENGTH)
    issuing_authority: str | None = Field(default=None, max_length=ISSUING_AUTHORITY_MAX_LENGTH)
    issue_date: date | None = None
    is_mandatory: bool = True
    pm_action_required: str | None = Field(default=None, max_length=ACTION_MAX_LENGTH)
    assigned_to: str | None = Field(default=None, max_length=ASSIGNEE_MAX_LENGTH)
    due_date: date | None = None
    notes: str | None = Field(default=None, max_length=NOTES_MAX_LENGTH)


class LegalDocumentUpdate(RequestModel):
    """Sửa mô tả hồ sơ. `stt`, `phase_group`, `maturity_status` không sửa qua đây."""

    doc_code_symbol: str | None = Field(default=None, max_length=DOC_CODE_MAX_LENGTH)
    doc_name: str | None = Field(default=None, min_length=1, max_length=DOC_NAME_MAX_LENGTH)
    issuing_authority: str | None = Field(default=None, max_length=ISSUING_AUTHORITY_MAX_LENGTH)
    issue_date: date | None = None
    is_mandatory: bool | None = None
    pm_action_required: str | None = Field(default=None, max_length=ACTION_MAX_LENGTH)
    assigned_to: str | None = Field(default=None, max_length=ASSIGNEE_MAX_LENGTH)
    due_date: date | None = None
    notes: str | None = Field(default=None, max_length=NOTES_MAX_LENGTH)

    @model_validator(mode="after")
    def _reject_null_for_required_fields(self) -> "LegalDocumentUpdate":
        for field_name in ("doc_name", "is_mandatory"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} không được để trống")
        return self


class LegalDocumentTransition(RequestModel):
    """`expected_status` là trạng thái client đang thấy; khác trạng thái thật thì trả 409."""

    expected_status: DocMaturityStatus
    target_status: DocMaturityStatus
    reason: str | None = Field(default=None, max_length=REASON_MAX_LENGTH)


class LegalDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    stt: int | None
    phase_group: LegalPhaseGroup
    doc_code_symbol: str | None
    doc_name: str
    issuing_authority: str | None
    issue_date: date | None
    is_mandatory: bool
    maturity_status: DocMaturityStatus
    pm_action_required: str | None
    assigned_to: str | None
    due_date: date | None
    notes: str | None


class LegalDocumentSummary(BaseModel):
    total: int
    by_status: dict[DocMaturityStatus, int]
    by_phase_group: dict[LegalPhaseGroup, dict[DocMaturityStatus, int]]
