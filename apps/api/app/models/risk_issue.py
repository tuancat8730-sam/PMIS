import uuid
from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.project import enum_values

RECORD_CODE_MAX_LENGTH = 100
CATEGORY_MAX_LENGTH = 100
STAKEHOLDER_MAX_LENGTH = 100
OWNER_MAX_LENGTH = 150


class RecordType(StrEnum):
    """Loại bản ghi; giá trị này cũng là LOẠI trong mã `{mã dự án}-{LOẠI}-{SỐ}`."""

    RISK = "RISK"
    ISSUE = "ISSUE"
    CR = "CR"
    NCR = "NCR"
    CONTRACT_DISCREPANCY = "CONTRACT_DISCREPANCY"


class RiskPriority(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RiskStatus(StrEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_INVESTOR = "WAITING_INVESTOR"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class RiskIssue(Base):
    __tablename__ = "project_risks_and_issues"
    __table_args__ = (UniqueConstraint("project_id", "code", name="uq_risk_issues_project_code"),)

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    record_type: Mapped[RecordType] = mapped_column(
        Enum(RecordType, name="risk_record_type", values_callable=enum_values),
    )
    code: Mapped[str] = mapped_column(String(RECORD_CODE_MAX_LENGTH))
    category: Mapped[str | None] = mapped_column(String(CATEGORY_MAX_LENGTH), default=None)
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    priority: Mapped[RiskPriority] = mapped_column(
        Enum(RiskPriority, name="risk_priority", values_callable=enum_values),
        default=RiskPriority.HIGH,
        server_default=text("'HIGH'"),
    )
    status: Mapped[RiskStatus] = mapped_column(
        Enum(RiskStatus, name="risk_status", values_callable=enum_values),
        default=RiskStatus.OPEN,
        server_default=text("'OPEN'"),
    )
    target_stakeholder: Mapped[str | None] = mapped_column(
        String(STAKEHOLDER_MAX_LENGTH), default=None
    )
    mitigation_action: Mapped[str | None] = mapped_column(Text, default=None)
    owner: Mapped[str | None] = mapped_column(String(OWNER_MAX_LENGTH), default=None)
    due_date: Mapped[date | None] = mapped_column(Date, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
