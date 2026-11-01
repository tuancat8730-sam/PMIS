import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

DRIVE_FILE_ID_MAX_LENGTH = 128
MIME_TYPE_MAX_LENGTH = 150


class DriveFile(Base):
    """Bản ghi file Drive đã đồng bộ về app (spec Phân hệ 3 mục 3, DDL `drive_files`).

    `extracted_text` và `ai_audit_summary` do E6 điền; E5 để NULL/mặc định.
    """

    __tablename__ = "drive_files"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    drive_file_id: Mapped[str] = mapped_column(String(DRIVE_FILE_ID_MAX_LENGTH), unique=True)
    drive_parent_id: Mapped[str | None] = mapped_column(String(DRIVE_FILE_ID_MAX_LENGTH))
    file_name: Mapped[str] = mapped_column(Text)
    drive_path: Mapped[str | None] = mapped_column(Text)
    mime_type: Mapped[str | None] = mapped_column(String(MIME_TYPE_MAX_LENGTH))
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    web_view_link: Mapped[str | None] = mapped_column(Text)
    modified_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extracted_text: Mapped[str | None] = mapped_column(Text)
    has_signature_or_stamp: Mapped[bool | None] = mapped_column(Boolean)
    ai_audit_summary: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
    )
