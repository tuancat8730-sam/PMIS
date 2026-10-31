import uuid
from enum import StrEnum

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.project import enum_values

CCCD_MASK_PREFIX = "********"


class PersonnelComplianceStatus(StrEnum):
    VERIFIED = "VERIFIED"
    DUPLICATE_ID_WARNING = "DUPLICATE_ID_WARNING"


class ContractPersonnel(Base):
    """Nhân sự chủ chốt. CCCD chỉ lưu dạng mã hóa; `national_id_last4` dùng để hiển thị."""

    __tablename__ = "contract_personnel"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contracts.id", ondelete="CASCADE"),
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(150))
    organization: Mapped[str | None] = mapped_column(String(150))
    position_role: Mapped[str] = mapped_column(String(200))
    national_id_encrypted: Mapped[str | None] = mapped_column(Text)
    national_id_last4: Mapped[str | None] = mapped_column(String(4))
    qualification: Mapped[str | None] = mapped_column(Text)
    is_backup_staff: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )
    compliance_status: Mapped[PersonnelComplianceStatus] = mapped_column(
        Enum(
            PersonnelComplianceStatus,
            name="personnel_compliance_status",
            values_callable=enum_values,
        ),
        default=PersonnelComplianceStatus.VERIFIED,
        server_default=text("'VERIFIED'"),
    )

    @property
    def national_id_masked(self) -> str | None:
        if self.national_id_last4 is None:
            return None
        return f"{CCCD_MASK_PREFIX}{self.national_id_last4}"
