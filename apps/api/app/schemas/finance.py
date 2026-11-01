from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.base import RequestModel

PERCENT_MAX = Decimal("100")
PERCENT_MAX_DIGITS = 5
PERCENT_DECIMAL_PLACES = 2
MONEY_MAX_DIGITS = 18
MONEY_DECIMAL_PLACES = 2
PLAN_YEAR_MIN = 2000
PLAN_YEAR_MAX = 2100

PacketStatus = Literal["NOT_STARTED", "IN_PROGRESS", "COMPLETE"]


class FinanceRuleCreate(RequestModel):
    guarantee_percent: Decimal = Field(
        gt=0, le=PERCENT_MAX, max_digits=PERCENT_MAX_DIGITS, decimal_places=PERCENT_DECIMAL_PLACES
    )
    advance_ceiling_percent: Decimal = Field(
        gt=0, le=PERCENT_MAX, max_digits=PERCENT_MAX_DIGITS, decimal_places=PERCENT_DECIMAL_PLACES
    )
    advance_working_days: int = Field(ge=1)
    lock_on: date
    lock_warning_days: int = Field(ge=0)
    non_working_days: list[date] = Field(default_factory=list)
    effective_from: date


class FinanceRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    guarantee_percent: Decimal
    advance_ceiling_percent: Decimal
    advance_working_days: int
    lock_on: date
    lock_warning_days: int
    non_working_days: list[date]
    effective_from: date


class GuaranteeCreate(RequestModel):
    issued_on: date
    expires_on: date
    poa_expires_on: date | None = None

    @model_validator(mode="after")
    def _check_expiry_after_issue(self) -> "GuaranteeCreate":
        if self.expires_on < self.issued_on:
            raise ValueError("Ngày hết hạn bảo lãnh phải sau hoặc bằng ngày phát hành")
        return self


class GuaranteeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    contract_id: UUID
    base_contract_value: Decimal
    percent: Decimal
    amount: Decimal
    issued_on: date
    expires_on: date
    poa_expires_on: date | None
    poa_expired_before_issue: bool


class AdvanceCreate(RequestModel):
    amount: Decimal = Field(gt=0, max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES)
    complete_packet_on: date
    decided_on: date

    @model_validator(mode="after")
    def _check_decision_after_packet(self) -> "AdvanceCreate":
        if self.decided_on < self.complete_packet_on:
            raise ValueError("Ngày quyết định tạm ứng phải sau hoặc bằng ngày nhận đủ hồ sơ")
        return self


class AdvanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    contract_id: UUID
    amount: Decimal
    complete_packet_on: date
    decided_on: date
    on_time: bool


class DisbursementCreate(RequestModel):
    contract_id: UUID
    plan_year: int = Field(ge=PLAN_YEAR_MIN, le=PLAN_YEAR_MAX)
    planned_amount: Decimal = Field(
        ge=0, max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES
    )


class DisbursementPaymentCreate(RequestModel):
    amount: Decimal = Field(gt=0, max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES)
    paid_on: date
    packet_status: PacketStatus | None = None


class DisbursementOut(BaseModel):
    id: UUID
    project_id: UUID
    contract_id: UUID
    plan_year: int
    planned_amount: Decimal
    paid_amount: Decimal
    paid_on: date | None
    packet_status: PacketStatus
    rate_percent: Decimal
    exceeds_plan: bool
    lock_warning_active: bool
    days_to_lock: int | None
