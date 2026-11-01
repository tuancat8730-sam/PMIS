from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import ANY_PROJECT_ROLE, SessionDep, WriteRateLimitDep, project_role_guard
from app.core.contract_discrepancy_rules import closing_requires_resolution
from app.core.rbac import Principal, Role, get_current_principal
from app.models.project import Project
from app.models.risk_issue import RecordType, RiskIssue
from app.schemas.risk_issues import RiskIssueCreate, RiskIssueOut, RiskIssueUpdate
from app.services.audit import record_audit
from app.services.risk_issues import (
    DuplicateRecordCodeError,
    create_risk_issue,
    get_risk_issue,
    list_risk_issues,
)

RISK_ISSUE_NOT_FOUND_DETAIL = "Không tìm thấy bản ghi rủi ro, CR hoặc NCR"
CONTRACT_DISCREPANCY_RESOLUTION_MESSAGE = (
    "Đóng mâu thuẫn hợp đồng cần nhập văn bản chốt của CĐT (resolution_ref)"
)

router = APIRouter(prefix="/projects/{project_id}/risk-issues", tags=["risk-issues"])


@router.post("", response_model=RiskIssueOut, status_code=status.HTTP_201_CREATED)
async def create_risk_issue_endpoint(
    project_id: UUID,
    payload: RiskIssueCreate,
    project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> RiskIssueOut:
    try:
        record = await create_risk_issue(
            session,
            project_id=project_id,
            project_code=project.code,
            values=payload.model_dump(),
        )
    except DuplicateRecordCodeError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Mã {exc} vừa được tạo bởi yêu cầu khác, vui lòng thử lại",
        ) from None

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="risk_issue.create",
        entity_type="risk_issue",
        entity_id=str(record.id),
        changes={"code": record.code, "record_type": record.record_type.value},
    )
    output = RiskIssueOut.model_validate(record)
    await session.commit()
    return output


@router.get("", response_model=list[RiskIssueOut])
async def list_risk_issues_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
    record_type: Annotated[RecordType | None, Query()] = None,
) -> list[RiskIssueOut]:
    records = await list_risk_issues(session, project_id, record_type)
    return [RiskIssueOut.model_validate(record) for record in records]


async def _get_risk_issue_or_404(
    session: SessionDep,
    project_id: UUID,
    risk_issue_id: UUID,
) -> RiskIssue:
    record = await get_risk_issue(session, project_id, risk_issue_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=RISK_ISSUE_NOT_FOUND_DETAIL
        )
    return record


@router.patch("/{risk_issue_id}", response_model=RiskIssueOut)
async def update_risk_issue_endpoint(
    project_id: UUID,
    risk_issue_id: UUID,
    payload: RiskIssueUpdate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> RiskIssueOut:
    record = await _get_risk_issue_or_404(session, project_id, risk_issue_id)
    changes = payload.model_dump(exclude_unset=True)
    target_status = changes.get("status", record.status)
    target_ref = changes.get("resolution_ref", record.resolution_ref)
    if closing_requires_resolution(record.record_type, target_status, target_ref):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=CONTRACT_DISCREPANCY_RESOLUTION_MESSAGE,
        )
    for field, value in changes.items():
        setattr(record, field, value)
    await session.flush()

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="risk_issue.update",
        entity_type="risk_issue",
        entity_id=str(record.id),
        changes={key: None if value is None else str(value) for key, value in changes.items()},
    )
    output = RiskIssueOut.model_validate(record)
    await session.commit()
    return output
