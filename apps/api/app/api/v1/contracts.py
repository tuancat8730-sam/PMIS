from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.deps import ANY_PROJECT_ROLE, SessionDep, WriteRateLimitDep, project_role_guard
from app.core.rbac import Principal, Role, get_current_principal
from app.models.contract import Contract
from app.models.project import Project
from app.schemas.contracts import ContractCreate, ContractOut
from app.services.audit import record_audit
from app.services.contracts import create_contract, list_contracts

router = APIRouter(prefix="/projects/{project_id}/contracts", tags=["contracts"])


@router.post("", response_model=ContractOut, status_code=status.HTTP_201_CREATED)
async def create_contract_endpoint(
    project_id: UUID,
    payload: ContractCreate,
    _project: Annotated[Project, Depends(project_role_guard(Role.PM))],
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: SessionDep,
    _rate_limit: WriteRateLimitDep,
) -> Contract:
    contract = await create_contract(session, project_id=project_id, payload=payload)

    await record_audit(
        session,
        actor_id=principal.user_id,
        action="contract.create",
        entity_type="contract",
        entity_id=str(contract.id),
        changes={"contract_number": contract.contract_number},
    )
    await session.commit()
    return contract


@router.get("", response_model=list[ContractOut])
async def list_contracts_endpoint(
    project_id: UUID,
    _project: Annotated[Project, Depends(project_role_guard(*ANY_PROJECT_ROLE))],
    session: SessionDep,
) -> list[Contract]:
    return await list_contracts(session, project_id)
