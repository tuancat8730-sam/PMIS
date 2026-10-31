from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role
from app.models.project_member import ProjectMember


class DuplicateMemberError(Exception):
    """Người dùng đã là thành viên của dự án."""


async def get_member_role(session: AsyncSession, project_id: UUID, user_id: UUID) -> Role | None:
    result = await session.execute(
        select(ProjectMember.role).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def add_member(
    session: AsyncSession,
    *,
    project_id: UUID,
    user_id: UUID,
    role: Role,
) -> ProjectMember:
    member = ProjectMember(project_id=project_id, user_id=user_id, role=role)
    session.add(member)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise DuplicateMemberError(str(user_id)) from exc
    return member


async def list_members(session: AsyncSession, project_id: UUID) -> list[ProjectMember]:
    result = await session.execute(
        select(ProjectMember)
        .where(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.role)
    )
    return list(result.scalars().all())
