import uuid

from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProjectTechnicalRequirement(Base):
    """Hạng mục kỹ thuật và chỉ tiêu nghiệm thu ràng buộc (báo cáo tổng quan, mục III)."""

    __tablename__ = "project_technical_requirements"
    __table_args__ = (
        UniqueConstraint("project_id", "item", name="uq_project_technical_requirements_item"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    item: Mapped[str] = mapped_column(Text)
    standard: Mapped[str | None] = mapped_column(Text)
    legal_basis: Mapped[str | None] = mapped_column(Text)
    solution: Mapped[str | None] = mapped_column(Text)
    responsibility: Mapped[str | None] = mapped_column(Text)
    acceptance_criteria: Mapped[str | None] = mapped_column(Text)
    related_risk: Mapped[str | None] = mapped_column(Text)
    monitoring_status: Mapped[str | None] = mapped_column(Text)
