import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.project import enum_values

HOLD_POINT_CODE_MAX_LENGTH = 10


class ConfirmingParty(StrEnum):
    """Ba bên phải xác nhận một điểm dừng H_x: CĐT, TVGS, Nhà thầu."""

    CDT = "CDT"
    TVGS = "TVGS"
    NHA_THAU = "NHA_THAU"


class HoldPoint(Base):
    __tablename__ = "hold_points"
    __table_args__ = (UniqueConstraint("project_id", "code", name="uq_hold_points_project_code"),)

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    milestone_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("milestones_wbs.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(HOLD_POINT_CODE_MAX_LENGTH))
    name: Mapped[str] = mapped_column(Text)


class HoldPointConfirmation(Base):
    __tablename__ = "hold_point_confirmations"
    __table_args__ = (
        UniqueConstraint("hold_point_id", "party", name="uq_hold_point_confirmations_party"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    hold_point_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("hold_points.id", ondelete="CASCADE"),
        index=True,
    )
    party: Mapped[ConfirmingParty] = mapped_column(
        Enum(ConfirmingParty, name="confirming_party", values_callable=enum_values),
    )
    confirmed_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
    )
    evidence_ref: Mapped[str] = mapped_column(Text)
    confirmed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
