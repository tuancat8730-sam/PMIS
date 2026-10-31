from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_member import ProjectMember
from app.schemas.projects import ProjectCreate


class DuplicateProjectCodeError(Exception):
    """Mã dự án đã tồn tại trong hệ thống."""


async def create_project(session: AsyncSession, *, payload: ProjectCreate) -> Project:
    project = Project(**payload.model_dump())
    session.add(project)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise DuplicateProjectCodeError(payload.code) from exc
    return project


async def list_projects(
    session: AsyncSession, *, member_user_id: UUID | None = None
) -> list[Project]:
    """Liệt kê dự án. Truyền `member_user_id` để chỉ lấy các dự án người đó là thành viên."""
    query = select(Project).order_by(Project.code)
    if member_user_id is not None:
        query = query.join(ProjectMember, ProjectMember.project_id == Project.id).where(
            ProjectMember.user_id == member_user_id
        )
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_project(session: AsyncSession, project_id: UUID) -> Project | None:
    return await session.get(Project, project_id)
