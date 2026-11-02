import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

FILE_FORMAT_MAX_LENGTH = 50
STORAGE_LOCATION_MAX_LENGTH = 100
SECURITY_OWNERSHIP_MAX_LENGTH = 150


class ProjectFileRegisterEntry(Base):
    """Một dòng danh mục quản trị file và bằng chứng nghiệm thu (sheet 5 báo cáo tracking)."""

    __tablename__ = "project_file_register"
    __table_args__ = (UniqueConstraint("project_id", "stt", name="uq_project_file_register_stt"),)

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    stt: Mapped[int] = mapped_column(Integer)
    folder_path: Mapped[str | None] = mapped_column(Text)
    file_name: Mapped[str] = mapped_column(Text)
    file_format: Mapped[str | None] = mapped_column(String(FILE_FORMAT_MAX_LENGTH))
    storage_location: Mapped[str | None] = mapped_column(String(STORAGE_LOCATION_MAX_LENGTH))
    purpose: Mapped[str | None] = mapped_column(Text)
    legal_status: Mapped[str | None] = mapped_column(Text)
    security_ownership: Mapped[str | None] = mapped_column(String(SECURITY_OWNERSHIP_MAX_LENGTH))
    next_action: Mapped[str | None] = mapped_column(Text)
    drive_file_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("drive_files.id", ondelete="SET NULL"),
    )
