import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EquipmentCatalog(Base):
    """Mã hàng trong phụ lục bảng giá của một dự án thiết bị, theo từng đợt giao."""

    __tablename__ = "equipment_catalog"
    __table_args__ = (
        CheckConstraint("contract_quantity >= 0", name="ck_equipment_catalog_quantity_nonnegative"),
        # G1: một dòng cho mỗi mã hàng trong một dự án và một đợt.
        UniqueConstraint(
            "project_id",
            "item_code",
            "category_batch",
            name="uq_equipment_catalog_project_item_batch",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    item_stt: Mapped[int | None] = mapped_column(Integer)
    item_code: Mapped[str] = mapped_column(String(100))
    item_name: Mapped[str] = mapped_column(Text)
    category_batch: Mapped[str] = mapped_column(String(50))
    brand: Mapped[str | None] = mapped_column(String(100))
    origin_country: Mapped[str | None] = mapped_column(String(100))
    manufacture_year: Mapped[int | None] = mapped_column(Integer)
    contract_quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    technical_specs: Mapped[dict] = mapped_column(JSONB)
    sample_approval_status: Mapped[str] = mapped_column(
        String(50), server_default=text("'PENDING'")
    )
    sample_serial_number: Mapped[str | None] = mapped_column(String(100))
    sample_inspection_data: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    co_cq_status: Mapped[str] = mapped_column(String(50), server_default=text("'MISSING'"))


class SampleInspection(Base):
    """Một lần kiểm định hàng mẫu. Kết quả 21 tiêu chí lưu trong JSONB (G2, Q2)."""

    __tablename__ = "sample_inspections"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("equipment_catalog.id", ondelete="CASCADE"), index=True
    )
    inspected_on: Mapped[date] = mapped_column(Date)
    inspector: Mapped[str] = mapped_column(String(150))
    serial_number_sample: Mapped[str | None] = mapped_column(String(150))
    criteria_results: Mapped[list] = mapped_column(JSONB)
    conclusion: Mapped[str] = mapped_column(String(50))
