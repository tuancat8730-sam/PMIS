import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core import guarantee_rules
from app.db.base import Base


class ContractGuarantee(Base):
    """Bảo lãnh thực hiện HĐ. Giá trị gốc chụp lúc phát hành, không đổi theo phụ lục."""

    __tablename__ = "contract_guarantees"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_contract_guarantees_amount_nonnegative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contracts.id", ondelete="CASCADE"),
        index=True,
    )
    base_contract_value: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    issued_on: Mapped[date] = mapped_column(Date)
    expires_on: Mapped[date] = mapped_column(Date)
    poa_expires_on: Mapped[date | None] = mapped_column(Date)

    @property
    def poa_expired_before_issue(self) -> bool:
        if self.poa_expires_on is None:
            return False
        return guarantee_rules.poa_expired_before_issue(self.issued_on, self.poa_expires_on)
