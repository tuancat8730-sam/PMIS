from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.project import ProjectArchetype, ProjectHealth
from app.schemas.base import RequestModel

PROJECT_CODE_PATTERN = r"^[A-Z0-9][A-Z0-9-]{2,49}$"
PROJECT_CODE_MAX_LENGTH = 50
PROJECT_NAME_MAX_LENGTH = 500
PROJECT_SHORT_NAME_MAX_LENGTH = 150
INVESTOR_NAME_MAX_LENGTH = 300
DECISION_AUTHORITY_MAX_LENGTH = 300
INVESTMENT_MAX_DIGITS = 18
INVESTMENT_DECIMAL_PLACES = 2
DRIVE_ID_MAX_LENGTH = 128


class ProjectCreate(RequestModel):
    code: str = Field(pattern=PROJECT_CODE_PATTERN, max_length=PROJECT_CODE_MAX_LENGTH)
    name: str = Field(min_length=1, max_length=PROJECT_NAME_MAX_LENGTH)
    short_name: str = Field(min_length=1, max_length=PROJECT_SHORT_NAME_MAX_LENGTH)
    archetype: ProjectArchetype
    investor_name: str = Field(min_length=1, max_length=INVESTOR_NAME_MAX_LENGTH)
    decision_authority: str | None = Field(default=None, max_length=DECISION_AUTHORITY_MAX_LENGTH)
    total_investment: Decimal = Field(
        gt=0,
        max_digits=INVESTMENT_MAX_DIGITS,
        decimal_places=INVESTMENT_DECIMAL_PLACES,
    )
    start_date: date | None = None
    end_date: date | None = None
    drive_root_folder_id: str | None = Field(
        default=None, min_length=1, max_length=DRIVE_ID_MAX_LENGTH
    )

    @model_validator(mode="after")
    def _check_date_order(self) -> "ProjectCreate":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("Ngày kết thúc phải sau hoặc bằng ngày bắt đầu")
        return self


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    short_name: str
    archetype: ProjectArchetype
    health_status: ProjectHealth
    investor_name: str
    decision_authority: str | None
    total_investment: Decimal
    start_date: date | None
    end_date: date | None
    drive_root_folder_id: str | None
    created_at: datetime
