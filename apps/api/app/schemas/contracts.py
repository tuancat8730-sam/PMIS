from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.base import RequestModel

PACKAGE_NAME_MAX_LENGTH = 500
CONTRACT_NUMBER_MAX_LENGTH = 100
CONTRACT_VALUE_MAX_DIGITS = 18
CONTRACT_VALUE_DECIMAL_PLACES = 2


class ContractCreate(RequestModel):
    package_name: str = Field(min_length=1, max_length=PACKAGE_NAME_MAX_LENGTH)
    contract_number: str | None = Field(default=None, max_length=CONTRACT_NUMBER_MAX_LENGTH)
    signed_date: date | None = None
    expiration_date: date | None = None
    contract_value: Decimal = Field(
        gt=0,
        max_digits=CONTRACT_VALUE_MAX_DIGITS,
        decimal_places=CONTRACT_VALUE_DECIMAL_PLACES,
    )

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
    contract_number: str | None
    signed_date: date | None
    expiration_date: date | None
    contract_value: Decimal
