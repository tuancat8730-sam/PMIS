import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Numeric, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ContractAdvance(Base):
    """Khoản tạm ứng đã duyệt. `on_time` cho biết có trong thời hạn ngày làm việc hay không."""

    __tablename__ = "contract_advances"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_contract_advances_amount_nonnegative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contracts.id", ondelete="CASCADE"),
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    complete_packet_on: Mapped[date] = mapped_column(Date)
    decided_on: Mapped[date] = mapped_column(Date)
    on_time: Mapped[bool] = mapped_column(Boolean)
