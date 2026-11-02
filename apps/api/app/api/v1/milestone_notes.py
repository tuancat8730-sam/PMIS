from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import SessionDep, WriteRateLimitDep, project_role_guard
from app.api.v1.milestones import MILESTONE_NOT_FOUND_DETAIL
from app.core.rbac import Principal, Role, get_current_principal
from app.models.project import Project
from app.schemas.milestone_children import NoteCreate, NoteOut
from app.services.audit import record_audit
from app.services.milestone_notes import add_note
from app.services.milestones import get_milestone

NOTE_WRITE_ROLES = (Role.PM, Role.SUPERVISION_CONSULTANT)

router = APIRouter(
    prefix="/projects/{project_id}/milestones/{milestone_id}/notes",
    tags=["milestone-notes"],
)


@router.post("", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def create_note_endpoint(
    project_id: UUID,
    milestone_id: UUID,
    payload: NoteCreate,
    _project: Annotated[Project, Depends(project_role_guard(*NOTE_WRITE_ROLES))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> NoteOut:
    milestone = await get_milestone(session, project_id, milestone_id)
    if milestone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=MILESTONE_NOT_FOUND_DETAIL
        )
    note = await add_note(
        session,
        milestone_id=milestone.id,
        body=payload.body,
        author_id=principal.user_id,
    )

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="milestone_note.create",
        entity_type="milestone_note",
        entity_id=str(note.id),
        changes={"milestone_id": str(milestone.id)},
    )
    output = NoteOut.from_note(note)
    await session.commit()
    return output
