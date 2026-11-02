from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import ANY_PROJECT_ROLE, SessionDep, project_role_guard
from app.models.project import Project
from app.schemas.project_technical_requirements import ProjectTechnicalRequirementOut
from app.services.project_technical_requirements import list_technical_requirements

router = APIRouter(
    prefix="/projects/{project_id}/technical-requirements",
    tags=["project-technical-requirements"],
)


@router.get("", response_model=list[ProjectTechnicalRequirementOut])
async def list_technical_requirements_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> list[ProjectTechnicalRequirementOut]:
    requirements = await list_technical_requirements(session, project_id)
    return [
        ProjectTechnicalRequirementOut.model_validate(requirement) for requirement in requirements
    ]
