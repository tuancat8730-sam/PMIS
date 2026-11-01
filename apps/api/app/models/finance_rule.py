import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import ARRAY, Date, ForeignKey, Integer, Numeric, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FinanceRule(Base):
    """Ngưỡng tài chính theo phiên bản: đổi ngưỡng tạo bản mới, không ghi đè bản cũ."""

    __tablename__ = "finance_rules"
    __table_args__ = (
        UniqueConstraint("project_id", "effective_from", name="uq_finance_rules_project_effective"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    guarantee_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    advance_ceiling_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    advance_working_days: Mapped[int] = mapped_column(Integer)
    lock_on: Mapped[date] = mapped_column(Date)
    lock_warning_days: Mapped[int] = mapped_column(Integer)
    non_working_days: Mapped[list[date]] = mapped_column(ARRAY(Date), server_default=text("'{}'"))
    effective_from: Mapped[date] = mapped_column(Date)
