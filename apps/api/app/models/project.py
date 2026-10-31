import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, DateTime, Enum, Numeric, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProjectArchetype(StrEnum):
    IT_SYSTEM = "IT_SYSTEM"
    GOODS_PROCUREMENT = "GOODS_PROCUREMENT"
    CONSTRUCTION = "CONSTRUCTION"
    HYBRID = "HYBRID"


class ProjectHealth(StrEnum):
    ON_TRACK = "ON_TRACK"
    AT_RISK = "AT_RISK"
    DELAYED = "DELAYED"
    CRITICAL = "CRITICAL"
    COMPLETED = "COMPLETED"


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [member.value for member in enum_cls]


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(Text)
    short_name: Mapped[str] = mapped_column(String(150))
    archetype: Mapped[ProjectArchetype] = mapped_column(
        Enum(ProjectArchetype, name="project_archetype", values_callable=enum_values),
    )
    health_status: Mapped[ProjectHealth] = mapped_column(
        Enum(ProjectHealth, name="project_health", values_callable=enum_values),
        default=ProjectHealth.ON_TRACK,
        server_default=text("'ON_TRACK'"),
    )
    investor_name: Mapped[str] = mapped_column(Text)
    decision_authority: Mapped[str | None] = mapped_column(Text)
    total_investment: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
