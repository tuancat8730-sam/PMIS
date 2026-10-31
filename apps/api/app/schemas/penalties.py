from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.base import RequestModel

RATE_PER_DAY_MAX = Decimal("0.01")
RATE_PER_DAY_MIN_EXCLUSIVE = Decimal("0")
CAP_PERCENT_MAX = Decimal("100")


class PenaltyRuleCreate(RequestModel):
    rate_per_day: Decimal = Field(gt=RATE_PER_DAY_MIN_EXCLUSIVE, le=RATE_PER_DAY_MAX)
    cap_percent: Decimal = Field(gt=RATE_PER_DAY_MIN_EXCLUSIVE, le=CAP_PERCENT_MAX)
    effective_from: date


class PenaltyRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    rate_per_day: Decimal
    cap_percent: Decimal
    effective_from: date


class PenaltyOut(BaseModel):
    milestone_id: UUID
    contract_id: UUID
    slippage_days: int
    rate_per_day: Decimal
    cap_percent: Decimal
    amount: Decimal
