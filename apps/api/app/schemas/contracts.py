from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.base import RequestModel

PACKAGE_NAME_MAX_LENGTH = 500
CONTRACT_NUMBER_MAX_LENGTH = 100
CONTRACT_VALUE_MAX_DIGITS = 18
CONTRACT_VALUE_DECIMAL_PLACES = 2
OVERVIEW_TEXT_MAX_LENGTH = 1000
ROLE_LABEL_MAX_LENGTH = 100


PackageKind = Literal["MAIN", "CONSULTING"]


class ContractCreate(RequestModel):
    package_name: str = Field(min_length=1, max_length=PACKAGE_NAME_MAX_LENGTH)
    package_kind: PackageKind = "MAIN"
    contract_number: str | None = Field(default=None, max_length=CONTRACT_NUMBER_MAX_LENGTH)
    signed_date: date | None = None
    expiration_date: date | None = None
    contract_value: Decimal = Field(
        gt=0,
        max_digits=CONTRACT_VALUE_MAX_DIGITS,
        decimal_places=CONTRACT_VALUE_DECIMAL_PLACES,
    )
    contractor_name: str | None = Field(default=None, max_length=OVERVIEW_TEXT_MAX_LENGTH)
    role_label: str | None = Field(default=None, max_length=ROLE_LABEL_MAX_LENGTH)
    contact_person: str | None = Field(default=None, max_length=OVERVIEW_TEXT_MAX_LENGTH)
    status_note: str | None = Field(default=None, max_length=OVERVIEW_TEXT_MAX_LENGTH)

    @model_validator(mode="after")
    def _check_date_order(self) -> "ContractCreate":
        if self.signed_date and self.expiration_date and self.expiration_date < self.signed_date:
            raise ValueError("Ngày hết hạn phải sau hoặc bằng ngày ký")
        return self


class ContractOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    package_name: str
    package_kind: str
    contract_number: str | None
    signed_date: date | None
    expiration_date: date | None
    contract_value: Decimal
    contractor_name: str | None
    role_label: str | None
    contact_person: str | None
    status_note: str | None
