import uuid
from datetime import date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.project import enum_values

MILESTONE_CODE_MAX_LENGTH = 30


class StoredMilestoneStatus(StrEnum):
    """Trạng thái người dùng chọn và được lưu trong DB."""

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class MilestoneStatus(StrEnum):
    """Trạng thái hiển thị: gồm cả AT_RISK và OVERDUE, suy ra khi đọc, không lưu."""

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    AT_RISK = "AT_RISK"
    OVERDUE = "OVERDUE"


class Milestone(Base):
    __tablename__ = "milestones_wbs"
    __table_args__ = (UniqueConstraint("project_id", "code", name="uq_milestones_project_code"),)

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    code: Mapped[str] = mapped_column(String(MILESTONE_CODE_MAX_LENGTH))
    name: Mapped[str] = mapped_column(Text)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("milestones_wbs.id", ondelete="SET NULL"),
        default=None,
    )
    baseline_start: Mapped[date | None] = mapped_column(Date, default=None)
    baseline_end: Mapped[date] = mapped_column(Date)
    adjusted_start: Mapped[date | None] = mapped_column(Date, default=None)
    adjusted_end: Mapped[date | None] = mapped_column(Date, default=None)
    actual_end: Mapped[date | None] = mapped_column(Date, default=None)
    is_hard_deadline: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )
    progress_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0"), server_default=text("0")
    )
    status: Mapped[StoredMilestoneStatus] = mapped_column(
        Enum(StoredMilestoneStatus, name="milestone_status", values_callable=enum_values),
        default=StoredMilestoneStatus.NOT_STARTED,
        server_default=text("'NOT_STARTED'"),
    )
    responsible_party: Mapped[str | None] = mapped_column(Text, default=None)
    evidence_summary: Mapped[str | None] = mapped_column(Text, default=None)
