import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MilestoneAdjustment(Base):
    """Điều chỉnh hạn của mốc đã khóa: không sửa trực tiếp, luôn có lý do và người thực hiện."""

    __tablename__ = "milestone_adjustments"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    milestone_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("milestones_wbs.id", ondelete="CASCADE"),
        index=True,
    )
    reason: Mapped[str] = mapped_column(Text)
    previous_end: Mapped[date] = mapped_column(Date)
    new_end: Mapped[date] = mapped_column(Date)
    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
