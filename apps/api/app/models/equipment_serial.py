import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EquipmentSerial(Base):
    """Số serial của từng bộ thiết bị. Serial là khóa duy nhất trong một dự án (G4)."""

    __tablename__ = "equipment_serials"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "serial_number_primary", name="uq_equipment_serials_project_primary"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("equipment_catalog.id", ondelete="CASCADE"), index=True
    )
    beneficiary_unit_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("beneficiary_units.id")
    )
    handover_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("delivery_handovers.id"))
    serial_number_primary: Mapped[str] = mapped_column(String(150))
    serial_number_secondary: Mapped[str | None] = mapped_column(String(150))
    batch_lot_code: Mapped[str | None] = mapped_column(String(100))
    co_cq_reference: Mapped[str | None] = mapped_column(String(150))
    verification_status: Mapped[str] = mapped_column(String(50), server_default=text("'IMPORTED'"))
    # Số phiên bản dùng phát hiện xung đột khi nhiều thiết bị cùng sửa (Q5, E10).
    version: Mapped[int] = mapped_column(Integer, server_default=text("1"), default=1)
