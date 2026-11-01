from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.it_statuses import PentestFixStatus, PentestSeverity, QaStatus, SurveyStatus
from app.core.nfr_rules import criteria_from_json
from app.schemas.base import RequestModel

MODULE_CODE_MAX_LENGTH = 20
MODULE_NAME_MAX_LENGTH = 200
CONTRACTOR_MAX_LENGTH = 150
UNIT_NAME_MAX_LENGTH = 200
LINK_MAX_LENGTH = 100
DESCRIPTION_MAX_LENGTH = 4000
METRIC_KEY_MAX_LENGTH = 100
PROGRESS_MIN = Decimal("0")
PROGRESS_MAX = Decimal("100")


def _reject_null_fields(model: BaseModel, names: tuple[str, ...]) -> None:
    for name in names:
        if name in model.model_fields_set and getattr(model, name) is None:
            raise ValueError(f"{name} không được để trống")


class ModuleCreate(RequestModel):
    module_code: str = Field(min_length=1, max_length=MODULE_CODE_MAX_LENGTH)
    module_name: str = Field(min_length=1, max_length=MODULE_NAME_MAX_LENGTH)
    responsible_contractor: str | None = Field(default=None, max_length=CONTRACTOR_MAX_LENGTH)
    dev_progress: Decimal = Field(default=Decimal("0"), ge=PROGRESS_MIN, le=PROGRESS_MAX)
    feature_checklist: list[Any] = Field(default_factory=list)
    nfr_metrics: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_nfr_metrics(self) -> "ModuleCreate":
        try:
            criteria_from_json(self.nfr_metrics)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        return self


class ModuleUpdate(RequestModel):
    module_name: str | None = Field(default=None, min_length=1, max_length=MODULE_NAME_MAX_LENGTH)
    responsible_contractor: str | None = Field(default=None, max_length=CONTRACTOR_MAX_LENGTH)
    dev_progress: Decimal | None = Field(default=None, ge=PROGRESS_MIN, le=PROGRESS_MAX)
    internal_qa_status: QaStatus | None = None
    uat_status: QaStatus | None = None

    @model_validator(mode="after")
    def _reject_null_required(self) -> "ModuleUpdate":
        _reject_null_fields(
            self, ("module_name", "dev_progress", "internal_qa_status", "uat_status")
        )
        return self


class ModuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    module_code: str
    module_name: str
    responsible_contractor: str | None
    dev_progress: Decimal
    internal_qa_status: str
    uat_status: str
    feature_checklist: list[Any]
    nfr_metrics: dict[str, Any]


class SurveyCreate(RequestModel):
    unit_name: str = Field(min_length=1, max_length=UNIT_NAME_MAX_LENGTH)
    status: SurveyStatus = SurveyStatus.NOT_STARTED
    survey_date: date | None = None
    minutes_document_id: UUID | None = None


class SurveyUpdate(RequestModel):
    status: SurveyStatus | None = None
    survey_date: date | None = None
    minutes_document_id: UUID | None = None

    @model_validator(mode="after")
    def _reject_null_required(self) -> "SurveyUpdate":
        _reject_null_fields(self, ("status",))
        return self


class SurveyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    unit_name: str
    status: str
    survey_date: date | None
    minutes_document_id: UUID | None


class RtmCreate(RequestModel):
    appendix_c_ref: str | None = Field(default=None, max_length=LINK_MAX_LENGTH)
    srs_ref: str | None = Field(default=None, max_length=LINK_MAX_LENGTH)
    module_code: str | None = Field(default=None, max_length=MODULE_CODE_MAX_LENGTH)
    test_case_ref: str | None = Field(default=None, max_length=LINK_MAX_LENGTH)


class RtmOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    appendix_c_ref: str | None
    srs_ref: str | None
    module_code: str | None
    test_case_ref: str | None


class RtmOrphanOut(BaseModel):
    row_index: int
    missing_links: list[str]


class PentestCreate(RequestModel):
    severity: PentestSeverity
    description: str = Field(min_length=1, max_length=DESCRIPTION_MAX_LENGTH)
    fix_status: PentestFixStatus = PentestFixStatus.OPEN
    rechecked_on: date | None = None


class PentestUpdate(RequestModel):
    fix_status: PentestFixStatus | None = None
    rechecked_on: date | None = None

    @model_validator(mode="after")
    def _reject_null_required(self) -> "PentestUpdate":
        _reject_null_fields(self, ("fix_status",))
        return self


class PentestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    severity: str
    description: str
    fix_status: str
    rechecked_on: date | None


class NfrMeasurementCreate(RequestModel):
    metric_key: str = Field(min_length=1, max_length=METRIC_KEY_MAX_LENGTH)
    measured: Decimal


class NfrMeasurementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    metric_key: str
    measured: Decimal
    measured_at: datetime
    recorded_by: UUID


class NfrResultOut(BaseModel):
    key: str
    passed: bool
    measured: Decimal | None


class NfrStatusOut(BaseModel):
    results: list[NfrResultOut]
    all_passed: bool
    acceptance_blockers: list[str]
