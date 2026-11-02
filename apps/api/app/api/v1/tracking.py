from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import ANY_PROJECT_ROLE, SessionDep, project_role_guard
from app.models.project import Project
from app.schemas.tracking import (
    RiskMatrixOut,
    RiskMatrixRow,
    ScheduleMatrixOut,
    ScheduleRowOut,
)
from app.services.milestone_notes import list_notes_by_milestone
from app.services.milestone_tasks import list_tasks_by_milestone
from app.services.tracking_matrix import list_risk_rows, list_schedule_rows

router = APIRouter(prefix="/projects/{project_id}", tags=["tracking"])


@router.get("/schedule-matrix", response_model=ScheduleMatrixOut)
async def schedule_matrix_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> ScheduleMatrixOut:
    today = date.today()
    milestones = await list_schedule_rows(session, project_id)
    milestone_ids = [milestone.id for milestone in milestones]
    tasks = await list_tasks_by_milestone(session, milestone_ids)
    notes = await list_notes_by_milestone(session, milestone_ids)
    rows = [
        ScheduleRowOut.build(milestone, today, tasks[milestone.id], notes[milestone.id])
        for milestone in milestones
    ]
    return ScheduleMatrixOut(total=len(rows), rows=rows)


@router.get("/risk-matrix", response_model=RiskMatrixOut)
async def risk_matrix_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> RiskMatrixOut:
    risks = await list_risk_rows(session, project_id)
    rows = [RiskMatrixRow.from_risk(risk) for risk in risks]
    rows.sort(key=lambda row: (-(row.score or 0), row.code))
    return RiskMatrixOut(total=len(rows), rows=rows)
