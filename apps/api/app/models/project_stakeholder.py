import uuid
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Enum, ForeignKey, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.project import enum_values


class StakeholderRole(StrEnum):
    INVESTOR = "INVESTOR"
    ACCEPTANCE_COMMITTEE = "ACCEPTANCE_COMMITTEE"
    PM_CONSULTANT = "PM_CONSULTANT"
    SUPERVISION_CONSULTANT = "SUPERVISION_CONSULTANT"
    MAIN_CONTRACTOR = "MAIN_CONTRACTOR"
    CONSORTIUM_MEMBER = "CONSORTIUM_MEMBER"
    BID_CONSULTANT = "BID_CONSULTANT"
    APPRAISAL_CONSULTANT = "APPRAISAL_CONSULTANT"


class ProjectStakeholder(Base):
    __tablename__ = "project_stakeholders"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    role: Mapped[StakeholderRole] = mapped_column(
        Enum(StakeholderRole, name="stakeholder_role", values_callable=enum_values),
    )
    organization_name: Mapped[str] = mapped_column(Text)
    tax_code: Mapped[str | None] = mapped_column(String(50))
    share_percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    responsibility_scope: Mapped[str | None] = mapped_column(Text)
    representative_name: Mapped[str | None] = mapped_column(String(150))
