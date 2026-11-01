from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import ANY_PROJECT_ROLE, SessionDep, WriteRateLimitDep, project_role_guard
from app.core.rbac import Principal, Role, get_current_principal
from app.models.project import Project
from app.schemas.finance import DisbursementCreate, DisbursementOut, DisbursementPaymentCreate
from app.services.audit import record_audit
from app.services.contracts import get_project_contract
from app.services.disbursements import (
    DuplicateDisbursementError,
    create_disbursement,
    disbursement_out,
    get_disbursement,
    list_disbursements,
    record_payment,
)
from app.services.finance import effective_finance_rule

CONTRACT_NOT_FOUND_DETAIL = "Không tìm thấy hợp đồng"
DISBURSEMENT_NOT_FOUND_DETAIL = "Không tìm thấy kế hoạch giải ngân"

router = APIRouter(prefix="/projects/{project_id}/disbursements", tags=["disbursements"])


@router.post("", response_model=DisbursementOut, status_code=status.HTTP_201_CREATED)
async def create_disbursement_endpoint(
    project_id: UUID,
    payload: DisbursementCreate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> DisbursementOut:
    contract = await get_project_contract(session, project_id, payload.contract_id)
    if contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=CONTRACT_NOT_FOUND_DETAIL)

    try:
        disbursement = await create_disbursement(session, project_id=project_id, payload=payload)
    except DuplicateDisbursementError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hợp đồng đã có kế hoạch giải ngân năm {exc}",
        ) from None

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="disbursement.create",
        entity_type="disbursement",
        entity_id=str(disbursement.id),
        changes={
            "plan_year": str(disbursement.plan_year),
            "planned_amount": str(disbursement.planned_amount),
        },
    )
    today = date.today()
    rule = await effective_finance_rule(session, project_id, today)
    output = disbursement_out(disbursement, rule, today)
    await session.commit()
    return output


@router.get("", response_model=list[DisbursementOut])
async def list_disbursements_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> list[DisbursementOut]:
    today = date.today()
    rule = await effective_finance_rule(session, project_id, today)
    disbursements = await list_disbursements(session, project_id)
    return [disbursement_out(item, rule, today) for item in disbursements]


@router.post("/{disbursement_id}/payments", response_model=DisbursementOut)
async def record_payment_endpoint(
    project_id: UUID,
    disbursement_id: UUID,
    payload: DisbursementPaymentCreate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> DisbursementOut:
    disbursement = await get_disbursement(session, project_id, disbursement_id)
    if disbursement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=DISBURSEMENT_NOT_FOUND_DETAIL
        )

    disbursement = await record_payment(session, disbursement=disbursement, payload=payload)
    await record_audit(
        session,
        actor_id=principal.user_id,
        action="disbursement.payment",
        entity_type="disbursement",
        entity_id=str(disbursement.id),
        changes={"amount": str(payload.amount), "paid_amount": str(disbursement.paid_amount)},
    )
    today = date.today()
    rule = await effective_finance_rule(session, project_id, today)
    output = disbursement_out(disbursement, rule, today)
    await session.commit()
    return output
