import uuid

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

LINK_MAX_LENGTH = 100
MODULE_CODE_MAX_LENGTH = 20


class RtmLink(Base):
    """Một dòng RTM: bốn mắt xích mã chuỗi (Phụ lục C, SRS, phân hệ, kịch bản test), theo Q3.

    Mắt xích để trống được phép lưu (dòng nháp); cổng nghiệm thu báo các dòng mồ côi.
    """

    __tablename__ = "rtm_links"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    appendix_c_ref: Mapped[str | None] = mapped_column(String(LINK_MAX_LENGTH), default=None)
    srs_ref: Mapped[str | None] = mapped_column(String(LINK_MAX_LENGTH), default=None)
    module_code: Mapped[str | None] = mapped_column(String(MODULE_CODE_MAX_LENGTH), default=None)
    test_case_ref: Mapped[str | None] = mapped_column(String(LINK_MAX_LENGTH), default=None)
