import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Disbursement(Base):
    """Kế hoạch vốn năm và số đã giải ngân của một hợp đồng. Mỗi hợp đồng có một dòng mỗi năm."""

    __tablename__ = "disbursements"
    __table_args__ = (
        UniqueConstraint("contract_id", "plan_year", name="uq_disbursements_contract_year"),
        CheckConstraint("planned_amount >= 0", name="ck_disbursements_planned_nonnegative"),
        CheckConstraint("paid_amount >= 0", name="ck_disbursements_paid_nonnegative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contracts.id", ondelete="CASCADE"),
        index=True,
    )
    plan_year: Mapped[int] = mapped_column(Integer)
    planned_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), server_default=text("0"))
    paid_on: Mapped[date | None] = mapped_column(Date)
    packet_status: Mapped[str] = mapped_column(String(20), server_default=text("'NOT_STARTED'"))
