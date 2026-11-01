from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import ANY_PROJECT_ROLE, SessionDep, WriteRateLimitDep, project_role_guard
from app.core.nfr_rules import all_passed
from app.core.rbac import Principal, Role, get_current_principal
from app.models.project import Project
from app.schemas.it_system import (
    NfrMeasurementCreate,
    NfrMeasurementOut,
    NfrResultOut,
    NfrStatusOut,
    PentestCreate,
    PentestOut,
    PentestUpdate,
)
from app.services.audit import record_audit
from app.services.it_gate import (
    it_completion_blockers_for_project,
    project_nfr_criteria,
    project_nfr_results,
)
from app.services.it_system import (
    apply_changes,
    create_pentest_finding,
    get_pentest_finding,
    list_pentest_findings,
    record_nfr_measurement,
)

PENTEST_NOT_FOUND_DETAIL = "Không tìm thấy lỗi pentest"
UNKNOWN_NFR_KEY_DETAIL = "Chỉ tiêu này chưa có ngưỡng NFR trong phân hệ"

router = APIRouter(prefix="/projects/{project_id}/it-system", tags=["it-system"])


@router.get("/pentest-findings", response_model=list[PentestOut])
async def list_pentest_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> list[PentestOut]:
    findings = await list_pentest_findings(session, project_id)
    return [PentestOut.model_validate(finding) for finding in findings]


@router.post("/pentest-findings", response_model=PentestOut, status_code=status.HTTP_201_CREATED)
async def create_pentest_endpoint(
    project_id: UUID,
    payload: PentestCreate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> PentestOut:
    finding = await create_pentest_finding(
        session, project_id=project_id, values=payload.model_dump()
    )
    await record_audit(
        session,
        actor_id=principal.user_id,
        action="it_pentest.create",
        entity_type="pentest_finding",
        entity_id=str(finding.id),
        changes={"severity": finding.severity, "fix_status": finding.fix_status},
    )
    output = PentestOut.model_validate(finding)
    await session.commit()
    return output


@router.patch("/pentest-findings/{finding_id}", response_model=PentestOut)
async def update_pentest_endpoint(
    project_id: UUID,
    finding_id: UUID,
    payload: PentestUpdate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> PentestOut:
    finding = await get_pentest_finding(session, project_id, finding_id)
    if finding is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=PENTEST_NOT_FOUND_DETAIL)
    changes = payload.model_dump(exclude_unset=True)
    apply_changes(finding, changes)
    await session.flush()

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="it_pentest.update",
        entity_type="pentest_finding",
        entity_id=str(finding.id),
        changes={key: str(value) for key, value in changes.items()},
    )
    output = PentestOut.model_validate(finding)
    await session.commit()
    return output


@router.post(
    "/nfr-measurements",
    response_model=NfrMeasurementOut,
    status_code=status.HTTP_201_CREATED,
)
async def record_nfr_endpoint(
    project_id: UUID,
    payload: NfrMeasurementCreate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> NfrMeasurementOut:
    criteria_keys = {criterion.key for criterion in await project_nfr_criteria(session, project_id)}
    if payload.metric_key not in criteria_keys:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=UNKNOWN_NFR_KEY_DETAIL,
        )
    measurement = await record_nfr_measurement(
        session,
        project_id=project_id,
        metric_key=payload.metric_key,
        measured=payload.measured,
        recorded_by=principal.user_id,
    )
    await record_audit(
        session,
        actor_id=principal.user_id,
        action="it_nfr.measure",
        entity_type="nfr_measurement",
        entity_id=str(measurement.id),
        changes={"metric_key": payload.metric_key, "measured": str(payload.measured)},
    )
    output = NfrMeasurementOut.model_validate(measurement)
    await session.commit()
    return output


@router.get("/nfr-status", response_model=NfrStatusOut)
async def nfr_status_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> NfrStatusOut:
    results = await project_nfr_results(session, project_id)
    blockers = await it_completion_blockers_for_project(session, project_id)
    return NfrStatusOut(
        results=[NfrResultOut.model_validate(result, from_attributes=True) for result in results],
        all_passed=all_passed(results),
        acceptance_blockers=list(blockers),
    )
