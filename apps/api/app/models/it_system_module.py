import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import ForeignKey, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

MODULE_CODE_MAX_LENGTH = 20
CONTRACTOR_MAX_LENGTH = 150
STATUS_MAX_LENGTH = 50
DEFAULT_QA_STATUS = "PENDING"


class ItSystemModule(Base):
    """Phân hệ phần mềm A–G của dự án CNTT (DDL `it_system_modules`, spec Phân hệ 5)."""

    __tablename__ = "it_system_modules"
    __table_args__ = (
        UniqueConstraint("project_id", "module_code", name="uq_it_system_modules_project_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    module_code: Mapped[str] = mapped_column(String(MODULE_CODE_MAX_LENGTH))
    module_name: Mapped[str] = mapped_column(Text)
    responsible_contractor: Mapped[str | None] = mapped_column(
        String(CONTRACTOR_MAX_LENGTH), default=None
    )
    dev_progress: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0"), server_default=text("0")
    )
    internal_qa_status: Mapped[str] = mapped_column(
        String(STATUS_MAX_LENGTH),
        default=DEFAULT_QA_STATUS,
        server_default=text(f"'{DEFAULT_QA_STATUS}'"),
    )
    uat_status: Mapped[str] = mapped_column(
        String(STATUS_MAX_LENGTH),
        default=DEFAULT_QA_STATUS,
        server_default=text(f"'{DEFAULT_QA_STATUS}'"),
    )
    feature_checklist: Mapped[list[Any]] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )
    nfr_metrics: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
