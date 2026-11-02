from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import ANY_PROJECT_ROLE, SessionDep, project_role_guard
from app.models.project import Project
from app.schemas.project_budget_items import ProjectBudgetItemOut
from app.services.project_budget_items import list_budget_items

router = APIRouter(
    prefix="/projects/{project_id}/budget-items",
    tags=["project-budget-items"],
)


@router.get("", response_model=list[ProjectBudgetItemOut])
async def list_budget_items_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> list[ProjectBudgetItemOut]:
    items = await list_budget_items(session, project_id)
    return [ProjectBudgetItemOut.model_validate(item) for item in items]
