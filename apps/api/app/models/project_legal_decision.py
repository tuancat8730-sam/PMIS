import uuid
from datetime import date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.project import enum_values

DECISION_NO_MAX_LENGTH = 100
ISSUING_AUTHORITY_MAX_LENGTH = 150


class LegalDecisionKind(StrEnum):
    """Loại quyết định hành chính của dự án (sheet 1 báo cáo tracking, mục I)."""

    PROJECT_APPROVAL = "PROJECT_APPROVAL"
    BCKTKT_APPROVAL = "BCKTKT_APPROVAL"
    BUDGET_APPROVAL = "BUDGET_APPROVAL"
    KHLCNT_APPROVAL = "KHLCNT_APPROVAL"
    BIDDING_RESULT_APPROVAL = "BIDDING_RESULT_APPROVAL"
    SUPERVISION_ASSIGNMENT = "SUPERVISION_ASSIGNMENT"


class ProjectLegalDecision(Base):
    __tablename__ = "project_legal_decisions"
    __table_args__ = (
        UniqueConstraint("project_id", "decision_no", name="uq_project_legal_decisions_no"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    kind: Mapped[LegalDecisionKind] = mapped_column(
        Enum(LegalDecisionKind, name="legal_decision_kind", values_callable=enum_values),
    )
    decision_no: Mapped[str] = mapped_column(String(DECISION_NO_MAX_LENGTH))
    decision_date: Mapped[date | None] = mapped_column(Date)
    issuing_authority: Mapped[str | None] = mapped_column(String(ISSUING_AUTHORITY_MAX_LENGTH))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    funding_source: Mapped[str | None] = mapped_column(Text)
    execution_period: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
