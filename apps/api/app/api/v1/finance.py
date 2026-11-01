from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ANY_PROJECT_ROLE, SessionDep, WriteRateLimitDep, project_role_guard
from app.core.rbac import Principal, Role, get_current_principal
from app.models.contract import Contract
from app.models.project import Project
from app.schemas.finance import (
    AdvanceCreate,
    AdvanceOut,
    FinanceRuleCreate,
    FinanceRuleOut,
    GuaranteeCreate,
    GuaranteeOut,
)
from app.services.audit import record_audit
from app.services.contracts import get_project_contract
from app.services.finance import (
    AdvanceCeilingExceededError,
    DuplicateFinanceRuleError,
    create_advance,
    create_finance_rule,
    create_guarantee,
    effective_finance_rule,
    list_advances,
    list_finance_rules,
    list_guarantees,
)

CONTRACT_NOT_FOUND_DETAIL = "Không tìm thấy hợp đồng"
NO_EFFECTIVE_RULE_DETAIL = "Chưa có ngưỡng tài chính có hiệu lực cho dự án"
ADVANCE_CEILING_DETAIL = "Tổng tạm ứng vượt trần tỷ lệ của hợp đồng"

router = APIRouter(prefix="/projects/{project_id}", tags=["finance"])


@router.post(
    "/finance-rules",
    response_model=FinanceRuleOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_finance_rule_endpoint(
    project_id: UUID,
    payload: FinanceRuleCreate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> FinanceRuleOut:
    try:
        rule = await create_finance_rule(session, project_id=project_id, payload=payload)
    except DuplicateFinanceRuleError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Đã có ngưỡng tài chính có hiệu lực từ {exc}",
        ) from None

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="finance_rule.create",
        entity_type="finance_rule",
        entity_id=str(rule.id),
        changes={
            "guarantee_percent": str(rule.guarantee_percent),
            "advance_ceiling_percent": str(rule.advance_ceiling_percent),
        },
    )
    output = FinanceRuleOut.model_validate(rule)
    await session.commit()
    return output


@router.get("/finance-rules", response_model=list[FinanceRuleOut])
async def list_finance_rules_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> list[FinanceRuleOut]:
    rules = await list_finance_rules(session, project_id)
    return [FinanceRuleOut.model_validate(rule) for rule in rules]


@router.post(
    "/contracts/{contract_id}/guarantees",
    response_model=GuaranteeOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_guarantee_endpoint(
    project_id: UUID,
    contract_id: UUID,
    payload: GuaranteeCreate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> GuaranteeOut:
    contract = await _project_contract_or_404(session, project_id, contract_id)
    rule = await effective_finance_rule(session, project_id, payload.issued_on)
    if rule is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=NO_EFFECTIVE_RULE_DETAIL
        )

    guarantee = await create_guarantee(session, contract=contract, rule=rule, payload=payload)
    await record_audit(
        session,
        actor_id=principal.user_id,
        action="guarantee.create",
        entity_type="contract_guarantee",
        entity_id=str(guarantee.id),
        changes={"amount": str(guarantee.amount), "percent": str(guarantee.percent)},
    )
    output = GuaranteeOut.model_validate(guarantee)
    await session.commit()
    return output


@router.get("/contracts/{contract_id}/guarantees", response_model=list[GuaranteeOut])
async def list_guarantees_endpoint(
    project_id: UUID,
    contract_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> list[GuaranteeOut]:
    await _project_contract_or_404(session, project_id, contract_id)
    guarantees = await list_guarantees(session, contract_id)
    return [GuaranteeOut.model_validate(guarantee) for guarantee in guarantees]


@router.post(
    "/contracts/{contract_id}/advances",
    response_model=AdvanceOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_advance_endpoint(
    project_id: UUID,
    contract_id: UUID,
    payload: AdvanceCreate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> AdvanceOut:
    contract = await _project_contract_or_404(session, project_id, contract_id)
    rule = await effective_finance_rule(session, project_id, payload.decided_on)
    if rule is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=NO_EFFECTIVE_RULE_DETAIL
        )

    try:
        advance = await create_advance(session, contract=contract, rule=rule, payload=payload)
    except AdvanceCeilingExceededError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=ADVANCE_CEILING_DETAIL
        ) from None

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="advance.create",
        entity_type="contract_advance",
        entity_id=str(advance.id),
        changes={"amount": str(advance.amount), "on_time": str(advance.on_time)},
    )
    output = AdvanceOut.model_validate(advance)
    await session.commit()
    return output


@router.get("/contracts/{contract_id}/advances", response_model=list[AdvanceOut])
async def list_advances_endpoint(
    project_id: UUID,
    contract_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> list[AdvanceOut]:
    await _project_contract_or_404(session, project_id, contract_id)
    advances = await list_advances(session, contract_id)
    return [AdvanceOut.model_validate(advance) for advance in advances]


async def _project_contract_or_404(
    session: AsyncSession,
    project_id: UUID,
    contract_id: UUID,
) -> Contract:
    contract = await get_project_contract(session, project_id, contract_id)
    if contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=CONTRACT_NOT_FOUND_DETAIL)
    return contract
