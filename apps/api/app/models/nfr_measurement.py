import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

METRIC_KEY_MAX_LENGTH = 100


class NfrMeasurement(Base):
    """Số đo thực tế của chỉ tiêu NFR. Lưu lịch sử; bản ghi mới nhất theo khóa là số hiện hành."""

    __tablename__ = "nfr_measurements"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    metric_key: Mapped[str] = mapped_column(String(METRIC_KEY_MAX_LENGTH))
    measured: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    recorded_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
    )
