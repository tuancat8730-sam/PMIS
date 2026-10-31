from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.project_stakeholder import StakeholderRole
from app.schemas.base import RequestModel

ORGANIZATION_NAME_MAX_LENGTH = 300
TAX_CODE_MAX_LENGTH = 50
REPRESENTATIVE_NAME_MAX_LENGTH = 150
MAX_SHARE_PERCENTAGE = 100
SHARE_MAX_DIGITS = 5
SHARE_DECIMAL_PLACES = 2


class StakeholderCreate(RequestModel):
    role: StakeholderRole
    organization_name: str = Field(min_length=1, max_length=ORGANIZATION_NAME_MAX_LENGTH)
    tax_code: str | None = Field(default=None, max_length=TAX_CODE_MAX_LENGTH)
    share_percentage: Decimal | None = Field(
        default=None,
        ge=0,
        le=MAX_SHARE_PERCENTAGE,
        max_digits=SHARE_MAX_DIGITS,
        decimal_places=SHARE_DECIMAL_PLACES,
    )
    responsibility_scope: str | None = None
    representative_name: str | None = Field(default=None, max_length=REPRESENTATIVE_NAME_MAX_LENGTH)


class StakeholderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    role: StakeholderRole
    organization_name: str
    tax_code: str | None
    share_percentage: Decimal | None
    responsibility_scope: str | None
    representative_name: str | None
