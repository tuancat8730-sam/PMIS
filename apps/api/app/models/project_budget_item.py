import uuid
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.project import enum_values


class BudgetCategory(StrEnum):
    """Khoản mục chi phí trong tổng mức đầu tư (báo cáo tổng quan, mục I)."""

    SOFTWARE = "SOFTWARE"
    PROJECT_MANAGEMENT = "PROJECT_MANAGEMENT"
    CONSULTING = "CONSULTING"
    OTHER = "OTHER"
    CONTINGENCY = "CONTINGENCY"


class ProjectBudgetItem(Base):
    __tablename__ = "project_budget_items"
    __table_args__ = (
        UniqueConstraint("project_id", "category", name="uq_project_budget_items_category"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    category: Mapped[BudgetCategory] = mapped_column(
        Enum(BudgetCategory, name="budget_category", values_callable=enum_values),
    )
    label: Mapped[str] = mapped_column(Text)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    note: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, server_default=text("0"))
