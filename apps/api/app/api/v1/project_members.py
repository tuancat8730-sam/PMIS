from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import ANY_PROJECT_ROLE, SessionDep, WriteRateLimitDep, project_role_guard
from app.core.rbac import Principal, Role, get_current_principal
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.project_members import MemberCreate, MemberOut
from app.services.audit import record_audit
from app.services.memberships import DuplicateMemberError, add_member, list_members

router = APIRouter(prefix="/projects/{project_id}/members", tags=["project-members"])

USER_NOT_FOUND_DETAIL = "Không tìm thấy người dùng"
DUPLICATE_MEMBER_DETAIL = "Người dùng đã là thành viên của dự án"


@router.post("", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
async def add_member_endpoint(
    payload: MemberCreate,
    project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> ProjectMember:
    if await session.get(User, payload.user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND_DETAIL)

    try:
        member = await add_member(
            session,
            project_id=project.id,
            user_id=payload.user_id,
            role=payload.role,
        )
    except DuplicateMemberError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=DUPLICATE_MEMBER_DETAIL,
        ) from None

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="project_member.add",
        entity_type="project_member",
        entity_id=str(member.id),
        changes={"user_id": str(payload.user_id), "role": payload.role.value},
    )
    await session.commit()
    return member


@router.get("", response_model=list[MemberOut])
async def list_members_endpoint(
    project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> list[ProjectMember]:
    return await list_members(session, project.id)
