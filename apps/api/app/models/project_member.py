import uuid

from sqlalchemy import Enum, ForeignKey, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.rbac import Role
from app.db.base import Base
from app.models.project import enum_values


class ProjectMember(Base):
    """Thành viên dự án và vai trò của họ trong dự án. Quyền toàn cục ADMIN không lưu ở đây."""

    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    role: Mapped[Role] = mapped_column(
        Enum(Role, name="project_member_role", values_callable=enum_values),
    )
