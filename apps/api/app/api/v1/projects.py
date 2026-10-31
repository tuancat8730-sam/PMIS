from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import (
    ANY_PROJECT_ROLE,
    SessionDep,
    WriteRateLimitDep,
    project_role_guard,
)
from app.core.rbac import Principal, Role, get_current_principal, require_roles
from app.models.project import Project
from app.schemas.projects import ProjectCreate, ProjectOut
from app.services.audit import record_audit
from app.services.memberships import add_member
from app.services.projects import DuplicateProjectCodeError, create_project, list_projects

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project_endpoint(
    payload: ProjectCreate,
    principal: Annotated[Principal, Depends(require_roles(Role.ADMIN, Role.PM))],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> Project:
    try:
        project = await create_project(session, payload=payload)
    except DuplicateProjectCodeError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Mã dự án đã tồn tại trong hệ thống",
        ) from None

    # Người tạo dự án là PM của dự án đó; việc này nằm trong cùng dòng audit `project.create`.
    await add_member(session, project_id=project.id, user_id=principal.user_id, role=Role.PM)
    await record_audit(
        session,
        actor_id=principal.user_id,
        action="project.create",
        entity_type="project",
        entity_id=str(project.id),
        changes={"code": project.code, "archetype": project.archetype.value},
    )
    await session.commit()
    return project


@router.get("", response_model=list[ProjectOut])
async def list_projects_endpoint(
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
) -> list[Project]:
    member_user_id = None if principal.role == Role.ADMIN else principal.user_id
    return await list_projects(session, member_user_id=member_user_id)


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project_endpoint(
    project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
) -> Project:
    return project
