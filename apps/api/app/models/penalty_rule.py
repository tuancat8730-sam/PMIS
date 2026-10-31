import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PenaltyRule(Base):
    """Ngưỡng phạt chậm tiến độ theo phiên bản: đổi ngưỡng tạo bản mới, không ghi đè bản cũ."""

    __tablename__ = "penalty_rules"
    __table_args__ = (
        UniqueConstraint("project_id", "effective_from", name="uq_penalty_rules_project_effective"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    rate_per_day: Mapped[Decimal] = mapped_column(Numeric(7, 6))
    cap_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    effective_from: Mapped[date] = mapped_column(Date)
