import uuid
from datetime import date
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.project import enum_values

DOC_CODE_MAX_LENGTH = 100
ISSUING_AUTHORITY_MAX_LENGTH = 150
ASSIGNEE_MAX_LENGTH = 150


class DocMaturityStatus(StrEnum):
    MISSING = "MISSING"
    DRAFT_DOCX = "DRAFT_DOCX"
    SUBMITTED_REVIEW = "SUBMITTED_REVIEW"
    WAITING_SIGNATURE = "WAITING_SIGNATURE"
    SIGNED_SCAN_PDF = "SIGNED_SCAN_PDF"
    DISCREPANCY_FOUND = "DISCREPANCY_FOUND"
    VERIFIED_CLOSED = "VERIFIED_CLOSED"


class LegalPhaseGroup(StrEnum):
    """5 giai đoạn chuẩn của Checklist hồ sơ pháp lý (spec Phân hệ 3 mục 1)."""

    PREPARATION = "PREPARATION"
    BIDDING = "BIDDING"
    CONTRACT_KICKOFF = "CONTRACT_KICKOFF"
    IMPLEMENTATION = "IMPLEMENTATION"
    ACCEPTANCE = "ACCEPTANCE"


class LegalDocument(Base):
    __tablename__ = "legal_documents"
    __table_args__ = (UniqueConstraint("project_id", "stt", name="uq_legal_documents_project_stt"),)

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    stt: Mapped[int | None] = mapped_column(Integer)
    phase_group: Mapped[LegalPhaseGroup] = mapped_column(
        Enum(LegalPhaseGroup, name="legal_phase_group", values_callable=enum_values),
    )
    doc_code_symbol: Mapped[str | None] = mapped_column(String(DOC_CODE_MAX_LENGTH))
    doc_name: Mapped[str] = mapped_column(Text)
    issuing_authority: Mapped[str | None] = mapped_column(String(ISSUING_AUTHORITY_MAX_LENGTH))
    issue_date: Mapped[date | None] = mapped_column(Date)
    is_mandatory: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
    )
    maturity_status: Mapped[DocMaturityStatus] = mapped_column(
        Enum(DocMaturityStatus, name="doc_maturity_status", values_callable=enum_values),
        default=DocMaturityStatus.MISSING,
        server_default=text("'MISSING'"),
    )
    pm_action_required: Mapped[str | None] = mapped_column(Text)
    assigned_to: Mapped[str | None] = mapped_column(String(ASSIGNEE_MAX_LENGTH))
    due_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
