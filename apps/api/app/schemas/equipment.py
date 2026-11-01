from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.base import RequestModel

ITEM_CODE_MAX_LENGTH = 100
ITEM_NAME_MAX_LENGTH = 500
ORIGIN_MAX_LENGTH = 100
BRAND_MAX_LENGTH = 100
CRITERION_CODE_MAX_LENGTH = 20
INSPECTOR_MAX_LENGTH = 150
SERIAL_MAX_LENGTH = 150
CRITERIA_MAX_COUNT = 50
MANUFACTURE_YEAR_MIN = 2000
MANUFACTURE_YEAR_MAX = 2100
MONEY_MAX_DIGITS = 18
MONEY_DECIMAL_PLACES = 2

BatchCode = Literal["DOT_1", "DOT_2", "DOT_3"]
CriterionResultValue = Literal["ĐẠT", "KHÔNG ĐẠT"]
DeliveryStatus = Literal[
    "SCHEDULED",
    "IN_TRANSIT",
    "INSTALLED",
    "SIGNED_HANDOVER",
    "ISSUE_REPORTED",
]


class EquipmentCatalogCreate(RequestModel):
    item_stt: int | None = Field(default=None, ge=1)
    item_code: str = Field(min_length=1, max_length=ITEM_CODE_MAX_LENGTH)
    item_name: str = Field(min_length=1, max_length=ITEM_NAME_MAX_LENGTH)
    category_batch: BatchCode
    brand: str | None = Field(default=None, max_length=BRAND_MAX_LENGTH)
    origin_country: str | None = Field(default=None, max_length=ORIGIN_MAX_LENGTH)
    manufacture_year: int | None = Field(
        default=None, ge=MANUFACTURE_YEAR_MIN, le=MANUFACTURE_YEAR_MAX
    )
    contract_quantity: int = Field(ge=0)
    unit_price: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
    )
    technical_specs: dict[str, str] = Field(default_factory=dict)


class EquipmentCatalogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    item_stt: int | None
    item_code: str
    item_name: str
    category_batch: str
    brand: str | None
    origin_country: str | None
    manufacture_year: int | None
    contract_quantity: int
    unit_price: Decimal | None
    technical_specs: dict[str, str]
    sample_approval_status: str
    sample_serial_number: str | None
    co_cq_status: str


class CriterionResultIn(RequestModel):
    code: str = Field(min_length=1, max_length=CRITERION_CODE_MAX_LENGTH)
    result: CriterionResultValue


class CriterionResultOut(BaseModel):
    code: str
    result: str


class SampleInspectionCreate(RequestModel):
    inspected_on: date
    inspector: str = Field(min_length=1, max_length=INSPECTOR_MAX_LENGTH)
    serial_number_sample: str | None = Field(default=None, max_length=SERIAL_MAX_LENGTH)
    criteria: list[CriterionResultIn] = Field(min_length=1, max_length=CRITERIA_MAX_COUNT)


class SampleInspectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    equipment_id: UUID
    inspected_on: date
    inspector: str
    serial_number_sample: str | None
    conclusion: str
    criteria_results: list[CriterionResultOut]


class DeliveryStatusUpdate(RequestModel):
    delivery_status: DeliveryStatus


class DeliveryHandoverOut(BaseModel):
    id: UUID
    beneficiary_unit_id: UUID
    cluster_code: str
    batch_code: str
    planned_date: date | None
    actual_date: date | None
    delivery_status: str
    version: int


class HandoverGenerateOut(BaseModel):
    created: int
