import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DeliveryHandover(Base):
    """Một dòng cho mỗi cặp (đơn vị, đợt), kể cả dòng tổng thể (G3)."""

    __tablename__ = "delivery_handovers"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "beneficiary_unit_id",
            "batch_code",
            name="uq_delivery_handovers_project_unit_batch",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    beneficiary_unit_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("beneficiary_units.id", ondelete="CASCADE"), index=True
    )
    batch_code: Mapped[str] = mapped_column(String(50))
    planned_date: Mapped[date | None] = mapped_column(Date)
    actual_date: Mapped[date | None] = mapped_column(Date)
    delivery_status: Mapped[str] = mapped_column(String(50), server_default=text("'SCHEDULED'"))
    generated_docx_drive_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("drive_files.id", ondelete="SET NULL")
    )
    signed_scan_drive_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("drive_files.id", ondelete="SET NULL")
    )
    site_photos: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    supervisor_name: Mapped[str | None] = mapped_column(String(150))
    inspector_notes: Mapped[str | None] = mapped_column(Text)
