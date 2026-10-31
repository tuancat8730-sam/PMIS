from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import ANY_PROJECT_ROLE, SessionDep, WriteRateLimitDep, project_role_guard
from app.core.rbac import Principal, Role, get_current_principal
from app.core.schedule_rules import effective_due_date, penalty_amount, slippage_days
from app.models.project import Project
from app.schemas.penalties import PenaltyOut, PenaltyRuleCreate, PenaltyRuleOut
from app.services.audit import record_audit
from app.services.contracts import get_contract
from app.services.milestones import get_milestone
from app.services.penalties import (
    DuplicatePenaltyRuleError,
    create_penalty_rule,
    effective_penalty_rule,
    list_penalty_rules,
)

CONTRACT_NOT_FOUND_DETAIL = "Không tìm thấy hợp đồng"
MILESTONE_NOT_FOUND_DETAIL = "Không tìm thấy mốc tiến độ"
NO_EFFECTIVE_RULE_DETAIL = "Chưa có ngưỡng phạt có hiệu lực cho dự án"

router = APIRouter(prefix="/projects/{project_id}", tags=["penalties"])


@router.post(
    "/penalty-rules",
    response_model=PenaltyRuleOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_penalty_rule_endpoint(
    project_id: UUID,
    payload: PenaltyRuleCreate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> PenaltyRuleOut:
    try:
        rule = await create_penalty_rule(
            session,
            project_id=project_id,
            values=payload.model_dump(),
        )
    except DuplicatePenaltyRuleError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Đã có ngưỡng phạt có hiệu lực từ {exc}",
        ) from None

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="penalty_rule.create",
        entity_type="penalty_rule",
        entity_id=str(rule.id),
        changes={"rate_per_day": str(rule.rate_per_day), "cap_percent": str(rule.cap_percent)},
    )
    output = PenaltyRuleOut.model_validate(rule)
    await session.commit()
    return output


@router.get("/penalty-rules", response_model=list[PenaltyRuleOut])
async def list_penalty_rules_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> list[PenaltyRuleOut]:
    rules = await list_penalty_rules(session, project_id)
    return [PenaltyRuleOut.model_validate(rule) for rule in rules]


@router.get("/milestones/{milestone_id}/penalty", response_model=PenaltyOut)
async def milestone_penalty_endpoint(
    project_id: UUID,
    milestone_id: UUID,
    contract_id: Annotated[UUID, Query()],
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> PenaltyOut:
    milestone = await get_milestone(session, project_id, milestone_id)
    if milestone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=MILESTONE_NOT_FOUND_DETAIL
        )
    contract = await get_contract(session, contract_id)
    if contract is None or contract.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=CONTRACT_NOT_FOUND_DETAIL)

    today = date.today()
    rule = await effective_penalty_rule(session, project_id, today)
    if rule is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=NO_EFFECTIVE_RULE_DETAIL,
        )
    due = effective_due_date(milestone.baseline_end, milestone.adjusted_end)
    days_late = slippage_days(due, milestone.actual_end, today)
    return PenaltyOut(
        milestone_id=milestone.id,
        contract_id=contract.id,
        slippage_days=days_late,
        rate_per_day=rule.rate_per_day,
        cap_percent=rule.cap_percent,
        amount=penalty_amount(
            contract.contract_value, days_late, rule.rate_per_day, rule.cap_percent
        ),
    )
