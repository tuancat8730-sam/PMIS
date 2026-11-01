import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

UNIT_NAME_MAX_LENGTH = 200
SURVEY_STATUS_MAX_LENGTH = 50
DEFAULT_SURVEY_STATUS = "NOT_STARTED"


class ItSurveyRecord(Base):
    """Khảo sát cuốn chiếu: một dòng cho mỗi đơn vị (trường hoặc phường), theo Q2."""

    __tablename__ = "it_survey_records"
    __table_args__ = (
        UniqueConstraint("project_id", "unit_name", name="uq_it_survey_records_project_unit"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    unit_name: Mapped[str] = mapped_column(String(UNIT_NAME_MAX_LENGTH))
    status: Mapped[str] = mapped_column(
        String(SURVEY_STATUS_MAX_LENGTH),
        default=DEFAULT_SURVEY_STATUS,
        server_default=text(f"'{DEFAULT_SURVEY_STATUS}'"),
    )
    survey_date: Mapped[date | None] = mapped_column(Date, default=None)
    minutes_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("legal_documents.id", ondelete="SET NULL"),
        default=None,
    )
