from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import ANY_PROJECT_ROLE, SessionDep, project_role_guard
from app.models.project import Project
from app.schemas.project_legal_decisions import ProjectLegalDecisionOut
from app.services.project_legal_decisions import list_legal_decisions

router = APIRouter(
    prefix="/projects/{project_id}/legal-decisions",
    tags=["project-legal-decisions"],
)


@router.get("", response_model=list[ProjectLegalDecisionOut])
async def list_legal_decisions_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> list[ProjectLegalDecisionOut]:
    decisions = await list_legal_decisions(session, project_id)
    return [ProjectLegalDecisionOut.model_validate(decision) for decision in decisions]
