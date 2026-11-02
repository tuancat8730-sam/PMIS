from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.project_budget_item import BudgetCategory
from app.schemas.base import RequestModel

LABEL_MAX_LENGTH = 200
NOTE_MAX_LENGTH = 1000


class ProjectBudgetItemCreate(RequestModel):
    """Dòng chi phí dùng khi nạp seed; chưa có API ghi."""

    category: BudgetCategory
    label: str = Field(min_length=1, max_length=LABEL_MAX_LENGTH)
    amount: Decimal = Field(ge=0)
    note: str | None = Field(default=None, max_length=NOTE_MAX_LENGTH)
    sort_order: int = 0


class ProjectBudgetItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    category: BudgetCategory
    label: str
    amount: Decimal
    note: str | None
    sort_order: int
