import uuid
from enum import StrEnum

from sqlalchemy import Enum, ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.project import enum_values

UNIT_CODE_MAX_LENGTH = 50
CLUSTER_CODE_MAX_LENGTH = 50
PERSON_NAME_MAX_LENGTH = 150
ROLE_MAX_LENGTH = 100
PHONE_MAX_LENGTH = 50
PROVINCE_MAX_LENGTH = 100


class UnitType(StrEnum):
    THPT = "THPT"
    THCS = "THCS"
    TIEU_HOC = "TIEU_HOC"
    PTDTNT = "PTDTNT"
    GDTX = "GDTX"
    UBND_PHUONG = "UBND_PHUONG"


class ReadinessStatus(StrEnum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SURVEYED = "SURVEYED"
    DELIVERED = "DELIVERED"
    ACCEPTED = "ACCEPTED"


class BeneficiaryUnit(Base):
    __tablename__ = "beneficiary_units"
    __table_args__ = (
        UniqueConstraint("project_id", "unit_code", name="uq_beneficiary_units_project_unit_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    unit_code: Mapped[str] = mapped_column(String(UNIT_CODE_MAX_LENGTH))
    official_name: Mapped[str] = mapped_column(Text)
    former_name: Mapped[str | None] = mapped_column(Text)
    unit_type: Mapped[UnitType] = mapped_column(
        Enum(UnitType, name="beneficiary_unit_type", values_callable=enum_values),
    )
    cluster_code: Mapped[str] = mapped_column(String(CLUSTER_CODE_MAX_LENGTH), index=True)
    cluster_name: Mapped[str | None] = mapped_column(Text)
    district_or_commune: Mapped[str | None] = mapped_column(Text)
    former_province: Mapped[str | None] = mapped_column(String(PROVINCE_MAX_LENGTH))
    address: Mapped[str | None] = mapped_column(Text)
    principal_name: Mapped[str | None] = mapped_column(String(PERSON_NAME_MAX_LENGTH))
    focal_point_name: Mapped[str | None] = mapped_column(String(PERSON_NAME_MAX_LENGTH))
    focal_point_role: Mapped[str | None] = mapped_column(String(ROLE_MAX_LENGTH))
    focal_point_phone: Mapped[str | None] = mapped_column(String(PHONE_MAX_LENGTH))
    readiness_status: Mapped[ReadinessStatus] = mapped_column(
        Enum(
            ReadinessStatus,
            name="beneficiary_readiness_status",
            values_callable=enum_values,
        ),
        server_default=ReadinessStatus.PENDING.value,
    )
