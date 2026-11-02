import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MilestoneNote(Base):
    """Nhật ký ghi chú của mốc: chỉ thêm, không sửa, không xóa. Có người viết và thời gian."""

    __tablename__ = "milestone_notes"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    milestone_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("milestones_wbs.id", ondelete="CASCADE"),
        index=True,
    )
    body: Mapped[str] = mapped_column(Text)
    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
